"""
GrooveBox - Route Blueprint per Album
=====================================
Definisce gli endpoint per le operazioni CRUD sul catalogo degli album 
e per l'upload/recupero delle copertine (immagini) da Supabase Storage.
"""

from flask import Blueprint, request, jsonify, g, redirect, current_app
from werkzeug.utils import secure_filename
from core.database import get_db
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
from utils.storage import upload_file, delete_file, get_public_url
from core.errors import BadRequestError, ForbiddenError, NotFoundError
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
    release_year = data.get("release_year")
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
    for col in ["title", "release_year", "genre"]:
        if col in data:
            val = data[col]
            if col == "genre" and val:
                val = val.strip() or None
            fields.append(f"{col} = %s")
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

    # Rimuovi la copertina dal bucket se nessun altro album la usa
    cover_path = album.get("cover_path")
    if cover_path:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM albums WHERE cover_path = %s;", (cover_path,))
            row = cursor.fetchone()
            count = row["total"] if row else 0
            if count == 0:
                delete_file("covers", cover_path)
        finally:
            cursor.close()

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

    ext = safe_original.rsplit(".", 1)[1].lower()
    filename = f"album_{album_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    file_bytes = file.read()
    if not upload_file("covers", filename, file_bytes, file.mimetype):
        raise BadRequestError("Errore durante il caricamento della copertina su Supabase Storage")

    old = album.get("cover_path")
    if old and old != filename:
        delete_file("covers", old)

    update_album_cover(album_id, filename)
    return jsonify({"status": "success", "cover_path": filename}), 200


@bp.route("/<int:album_id>/cover", methods=["GET"])
def get_cover(album_id):
    """Serve il file immagine della copertina associato all'album."""
    album = find_album_by_id(album_id)
    if not album or not album.get("cover_path"):
        raise NotFoundError("Copertina non trovata")
        
    url = get_public_url("covers", album["cover_path"])
    return redirect(url)
