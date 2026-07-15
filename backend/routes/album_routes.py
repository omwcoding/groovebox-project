"""
GrooveBox - Route Blueprint per Album
=====================================
Definisce gli endpoint per le operazioni CRUD sul catalogo degli album 
e per l'upload/recupero delle copertine (immagini).
"""

from flask import Blueprint, request, jsonify, g, send_from_directory, current_app
from werkzeug.utils import secure_filename
from core.auth import token_required, require_role
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
    """Verifica se l'estensione del file rientra nei formati consentiti."""
    allowed_exts = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts


@bp.route("", methods=["GET"])
@token_required
def get_albums():
    """Restituisce la lista di tutti gli album del catalogo."""
    albums = get_all_albums()
    return jsonify({"status": "success", "data": albums})


@bp.route("/<int:album_id>", methods=["GET"])
@token_required
def get_album(album_id):
    """Restituisce i dettagli di un singolo album tramite ID."""
    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")
    return jsonify({"status": "success", "data": album})


@bp.route("", methods=["POST"])
@token_required
@require_role("collector")
def create_album():
    """Registra un nuovo album nel catalogo globale (autorizzato solo per ruolo 'collector')."""

    data = request.get_json()
    validate_json_payload(data, ["title"])

    title = data["title"].strip()
    release_year = data.get("releaseYear")
    genre = (data.get("genre") or "").strip() or None
    artist_ids = data.get("artist_ids", [])



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


@bp.route("/<int:album_id>", methods=["PUT"])
@token_required
@require_role("administrator")
def update_album(album_id):
    """Aggiorna le informazioni di un album a catalogo (autorizzato solo per ruolo 'administrator')."""

    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    fields = []
    values = []
    for col in ["title", "releaseYear", "genre"]:
        if col in data:
            val = data[col]
            if col == "genre" and val:
                val = val.strip() or None
            fields.append(f"{col} = ?")
            values.append(val.strip() if isinstance(val, str) else val)

    artist_ids = None
    if "artist_ids" in data:
        artist_ids = data["artist_ids"]
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


@bp.route("/<int:album_id>", methods=["DELETE"])
@token_required
@require_role("administrator")
def delete_album(album_id):
    """Elimina definitivamente un album dal catalogo (autorizzato solo per ruolo 'administrator')."""

    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")

    delete_album_by_id(album_id)

    # Rimuovi la copertina dal disco se nessun altro album la usa
    cover_path = album.get("coverPath")
    if cover_path:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM ALBUM WHERE coverPath = ?", (cover_path,)).fetchone()[0]
        if count == 0:
            filepath = os.path.join(current_app.config["COVERS_FOLDER"], cover_path)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    current_app.logger.warning(f"Errore rimozione copertina {filepath}: {e}")

    return jsonify({
        "status": "success",
        "message": "Album eliminato dal catalogo con successo"
    })


@bp.route("/<int:album_id>/cover", methods=["POST"])
@token_required
@require_role("collector", "administrator")
def upload_cover(album_id):
    """Carica o sostituisce l'immagine di copertina per l'album specificato."""
    album = find_album_by_id(album_id)
    if not album:
        raise NotFoundError("Album non trovato")

    role = g.current_user["role"]
    if role == "collector" and album["id_user"] != g.current_user["id_user"]:
        raise ForbiddenError("Non autorizzato ad aggiornare la copertina di questo album")

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


@bp.route("/<int:album_id>/cover", methods=["GET"])
def get_cover(album_id):
    """Serve il file immagine della copertina associato all'album."""
    album = find_album_by_id(album_id)
    if not album or not album.get("coverPath"):
        raise NotFoundError("Copertina non trovata")
        
    upload_dir = current_app.config["COVERS_FOLDER"]
    return send_from_directory(upload_dir, album["coverPath"])
