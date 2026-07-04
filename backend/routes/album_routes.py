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
from auth import token_required
from dal.album_dal import (
    get_all_albums,
    find_album_by_id,
    insert_album,
    update_album_data,
    delete_album_by_id,
    update_album_cover
)
from dal.artist_dal import find_artist_by_id
import os
import uuid

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

bp = Blueprint("albums", __name__, url_prefix="/api/albums")


# --------------------------------------------------------------------------
# GET /api/albums
# Restituisce tutti gli album del catalogo (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_albums():
    try:
        albums = get_all_albums()
        return jsonify({"status": "success", "data": albums})
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento degli album"}), 500


# --------------------------------------------------------------------------
# GET /api/albums/<id>
# Dettaglio di un singolo album (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["GET"])
@token_required
def get_album(album_id):
    try:
        album = find_album_by_id(album_id)
        if not album:
            return jsonify({"status": "error", "message": "Album non trovato"}), 404
        return jsonify({"status": "success", "data": album})
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento dell'album"}), 500


# --------------------------------------------------------------------------
# POST /api/albums
# Inserisce un nuovo album nel catalogo (solo Collector).
# Body JSON: { title, releaseYear?, genre?, artist_ids?: [int] }
# --------------------------------------------------------------------------
@bp.route("", methods=["POST"])
@token_required
def create_album():
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Solo i Collector possono inserire nuovi album"
        }), 403

    data = request.get_json()
    if not data or not data.get("title", "").strip():
        return jsonify({
            "status": "error",
            "message": "Il campo 'title' e' obbligatorio"
        }), 400

    title = data["title"].strip()
    release_year = data.get("releaseYear")
    genre = data.get("genre", "").strip() or None
    artist_ids = data.get("artist_ids", [])

    try:
        # Verifica che gli artist_ids esistano
        for aid in artist_ids:
            artist = find_artist_by_id(aid)
            if not artist:
                return jsonify({
                    "status": "error",
                    "message": f"Artista con id {aid} non trovato"
                }), 404

        album_id = insert_album(title, release_year, genre, artist_ids, g.current_user["id_user"])
        album = find_album_by_id(album_id)
        
        return jsonify({
            "status": "success",
            "message": "Album inserito nel catalogo con successo",
            "data": album
        }), 201
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante la creazione dell'album"}), 500


# --------------------------------------------------------------------------
# PUT /api/albums/<id>
# Modifica un album esistente (solo Admin).
# Body JSON: { title?, releaseYear?, genre?, artist_ids?: [int] }
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["PUT"])
@token_required
def update_album(album_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono modificare gli album"
        }), 403

    try:
        album = find_album_by_id(album_id)
        if not album:
            return jsonify({"status": "error", "message": "Album non trovato"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Nessun dato fornito"}), 400

        # Aggiornamento campi
        fields = []
        values = []
        for col in ["title", "releaseYear", "genre"]:
            if col in data:
                fields.append(f"{col} = ?")
                val = data[col]
                values.append(val.strip() if isinstance(val, str) else val)

        artist_ids = None
        if "artist_ids" in data:
            artist_ids = data["artist_ids"]
            # Verifica esistenza artisti
            for aid in artist_ids:
                a = find_artist_by_id(aid)
                if not a:
                    return jsonify({
                        "status": "error",
                        "message": f"Artista con id {aid} non trovato"
                    }), 404

        updated_album = update_album_data(album_id, fields, values, artist_ids)
        return jsonify({
            "status": "success",
            "message": "Album aggiornato con successo",
            "data": updated_album
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante la modifica dell'album"}), 500


# --------------------------------------------------------------------------
# DELETE /api/albums/<id>
# Elimina un album dal catalogo (solo Admin).
# Rimuove anche le associazioni ALBUM_ARTIST e le PHYSICAL_COPY collegate (via ON DELETE CASCADE).
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["DELETE"])
@token_required
def delete_album(album_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono eliminare gli album"
        }), 403

    try:
        album = find_album_by_id(album_id)
        if not album:
            return jsonify({"status": "error", "message": "Album non trovato"}), 404

        delete_album_by_id(album_id)
        return jsonify({
            "status": "success",
            "message": "Album eliminato dal catalogo con successo"
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante l'eliminazione dell'album"}), 500


# --------------------------------------------------------------------------
# POST /api/albums/<id>/cover
# Carica una copertina per l'album (Collector proprietario o Admin).
# Form-data: file = <image>
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>/cover", methods=["POST"])
@token_required
def upload_cover(album_id):
    try:
        album = find_album_by_id(album_id)
        if not album:
            return jsonify({"status": "error", "message": "Album non trovato"}), 404

        role = g.current_user["role"]
        if role == "collector" and album["id_user"] != g.current_user["id_user"]:
            return jsonify({"status": "error", "message": "Non autorizzato"}), 403
        if role not in ("collector", "administrator"):
            return jsonify({"status": "error", "message": "Non autorizzato"}), 403

        if "file" not in request.files:
            return jsonify({"status": "error", "message": "Nessun file fornito"}), 400

        file = request.files["file"]
        if file.filename == "" or not _allowed(file.filename):
            return jsonify({"status": "error", "message": "Formato non supportato (jpg, png, webp)"}), 400

        upload_dir = os.path.join(current_app.root_path, "uploads", "covers")
        os.makedirs(upload_dir, exist_ok=True)

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"album_{album_id}_{uuid.uuid4().hex[:8]}.{ext}"
        file.save(os.path.join(upload_dir, filename))

        # Rimuove copertina precedente se diversa
        old = album.get("coverPath")
        if old and old != filename:
            old_path = os.path.join(upload_dir, old)
            if os.path.exists(old_path):
                os.remove(old_path)

        update_album_cover(album_id, filename)
        return jsonify({"status": "success", "coverPath": filename}), 200
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante il caricamento della copertina"}), 500


# --------------------------------------------------------------------------
# GET /api/albums/<id>/cover
# Serve il file immagine della copertina.
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>/cover", methods=["GET"])
def get_cover(album_id):
    try:
        album = find_album_by_id(album_id)
        if not album or not album.get("coverPath"):
            return jsonify({"status": "error", "message": "Nessuna copertina"}), 404
        upload_dir = os.path.join(current_app.root_path, "uploads", "covers")
        return send_from_directory(upload_dir, album["coverPath"])
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante il caricamento dell'immagine"}), 500
