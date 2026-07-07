"""
GrooveBox - Rotte Album
========================
Blueprint: /api/albums

Matrice di visibilita' (doc 3.4):
  Collector     -> ALBUM: ALL scope, CR__  (crea e consulta)
  Administrator -> ALBUM: ALL scope, CRUD  (gestione completa catalogo)

Gestisce anche la relazione PUBLISHES (ALBUM_ARTIST) in modo trasparente.
"""

from flask import Blueprint, request, jsonify, g, send_from_directory, current_app
from werkzeug.utils import secure_filename
from core.auth import token_required
from dal.album_dal import (
    get_all_albums,
    find_album_by_id,
    insert_album,
    update_album_data,
    delete_album_by_id,
    update_album_cover
)
from dal.artist_dal import find_artist_by_id
from utils.validators import validate_json_payload
from core.errors import BadRequestError, ForbiddenError, NotFoundError
import os
import uuid

bp = Blueprint("albums", __name__, url_prefix="/api/albums")


def _allowed(filename):
    allowed_exts = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts


# --------------------------------------------------------------------------
# GET /api/albums
# Restituisce tutti gli album del catalogo (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_albums():
    albums = get_all_albums()
    return jsonify({"status": "success", "data": albums})


# --------------------------------------------------------------------------
# GET /api/albums/<id>
# Dettaglio di un singolo album (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["GET"])
@token_required
def get_album(album_id):
    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")
    return jsonify({"status": "success", "data": album})


# --------------------------------------------------------------------------
# POST /api/albums
# Inserisce un nuovo album nel catalogo (solo Collector).
# Body JSON: { title, releaseYear?, genre?, artist_ids?: [int] }
# --------------------------------------------------------------------------
@bp.route("", methods=["POST"])
@token_required
def create_album():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Solo i Collector possono inserire nuovi album")

    data = request.get_json()
    validate_json_payload(data, ["title"])

    title = data["title"].strip()
    release_year = data.get("releaseYear")
    genre = data.get("genre", "").strip() or None
    artist_ids = data.get("artist_ids", [])

    if genre and genre not in current_app.config["ALLOWED_GENRES"]:
        raise BadRequestError(f"Genere musicale '{genre}' non valido o non consentito")

    # Verifica che gli artist_ids esistano
    for aid in artist_ids:
        artist = find_artist_by_id(aid)
        if not artist:
            raise NotFoundError(f"Artista con id {aid} non trovato")

    album_id = insert_album(title, release_year, genre, artist_ids, g.current_user["id_user"])
    album = find_album_by_id(album_id)
    
    return jsonify({
        "status": "success",
        "message": "Album inserito nel catalogo con successo",
        "data": album
    }), 201


# --------------------------------------------------------------------------
# PUT /api/albums/<id>
# Modifica un album esistente (solo Admin).
# Body JSON: { title?, releaseYear?, genre?, artist_ids?: [int] }
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["PUT"])
@token_required
def update_album(album_id):
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Solo gli amministratori possono modificare gli album")

    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    # Aggiornamento campi
    fields = []
    values = []
    for col in ["title", "releaseYear", "genre"]:
        if col in data:
            val = data[col]
            if col == "genre" and val:
                val = val.strip() or None
                if val and val not in current_app.config["ALLOWED_GENRES"]:
                    raise BadRequestError(f"Genere musicale '{val}' non valido o non consentito")
            fields.append(f"{col} = ?")
            values.append(val.strip() if isinstance(val, str) else val)

    artist_ids = None
    if "artist_ids" in data:
        artist_ids = data["artist_ids"]
        # Verifica esistenza artisti
        for aid in artist_ids:
            a = find_artist_by_id(aid)
            if not a:
                raise NotFoundError(f"Artista con id {aid} non trovato")

    updated_album = update_album_data(album_id, fields, values, artist_ids)
    return jsonify({
        "status": "success",
        "message": "Album aggiornato con successo",
        "data": updated_album
    })


# --------------------------------------------------------------------------
# DELETE /api/albums/<id>
# Elimina un album dal catalogo (solo Admin).
# Rimuove anche le associazioni ALBUM_ARTIST e le PHYSICAL_COPY collegate (via ON DELETE CASCADE).
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["DELETE"])
@token_required
def delete_album(album_id):
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Solo gli amministratori possono eliminare gli album")

    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")

    delete_album_by_id(album_id)
    return jsonify({
        "status": "success",
        "message": "Album eliminato dal catalogo con successo"
    })


# --------------------------------------------------------------------------
# POST /api/albums/<id>/cover
# Carica una copertina per l'album (Collector proprietario o Admin).
# Form-data: file = <image>
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>/cover", methods=["POST"])
@token_required
def upload_cover(album_id):
    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")

    role = g.current_user["role"]
    if role == "collector" and album["id_user"] != g.current_user["id_user"]:
        raise ForbiddenError("Non autorizzato ad aggiornare la copertina di questo album")
    if role not in ("collector", "administrator"):
        raise ForbiddenError("Non autorizzato")

    if "file" not in request.files:
        raise BadRequestError("Nessun file fornito nella richiesta")

    file = request.files["file"]
    safe_original = secure_filename(file.filename)
    if not safe_original or not _allowed(safe_original):
        raise BadRequestError("Formato copertina non supportato (ammessi: jpg, png, webp)")

    upload_dir = current_app.config["COVERS_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    ext = safe_original.rsplit(".", 1)[1].lower()
    filename = f"album_{album_id}_{uuid.uuid4().hex[:8]}.{ext}"
    file.save(os.path.join(upload_dir, filename))

    # Rimuove copertina precedente se diversa
    old = album.get("coverPath")
    if old and old != filename:
        old_path = os.path.join(upload_dir, old)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                current_app.logger.warning(f"Impossibile rimuovere la vecchia copertina {old_path}: {e}")

    update_album_cover(album_id, filename)
    return jsonify({"status": "success", "coverPath": filename}), 200


# --------------------------------------------------------------------------
# GET /api/albums/<id>/cover
# Serve il file immagine della copertina.
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>/cover", methods=["GET"])
def get_cover(album_id):
    album = find_album_by_id(album_id)
    if not album or not album.get("coverPath"):
        raise NotFoundError("Copertina non trovata")
        
    upload_dir = current_app.config["COVERS_FOLDER"]
    return send_from_directory(upload_dir, album["coverPath"])
