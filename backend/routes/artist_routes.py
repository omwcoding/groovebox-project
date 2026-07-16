"""
GrooveBox - Route Blueprint per Artisti
=======================================
Definisce gli endpoint per le operazioni CRUD sul catalogo degli artisti
e per la consultazione della relativa discografia da Supabase Storage.
"""

from flask import Blueprint, request, jsonify, g, redirect, current_app
from core.database import get_db
from core.auth import token_required, require_role
from dal.artist_dal import (
    get_all_artists,
    find_artist_by_id,
    get_artist_albums,
    insert_artist,
    update_artist_name,
    delete_artist_by_id
)
from utils.validators import validate_json_payload
from utils.storage import delete_file, get_public_url
from core.errors import ForbiddenError, NotFoundError

bp = Blueprint("artists", __name__, url_prefix="/api/artists")


@bp.route("", methods=["GET"])
@token_required
def get_artists():
    """Restituisce l'elenco completo degli artisti presenti nel catalogo."""
    artists = get_all_artists()
    return jsonify({
        "status": "success",
        "data": [dict(a) for a in artists]
    })


@bp.route("/<int:artist_id>", methods=["GET"])
@token_required
def get_artist(artist_id):
    """Restituisce i dettagli dell'artista specificato e la sua discografia associata."""
    artist = find_artist_by_id(artist_id)
    if not artist:
        raise NotFoundError("Artista non trovato")

    result = dict(artist)
    albums = get_artist_albums(artist_id)
    result["albums"] = [dict(al) for al in albums]

    return jsonify({"status": "success", "data": result})


@bp.route("", methods=["POST"])
@token_required
def create_artist():
    """Registra un nuovo artista nel catalogo globale."""
    data = request.get_json()
    validate_json_payload(data, ["name"])

    name = data["name"].strip()
    artist_id = insert_artist(name)
    
    return jsonify({
        "status": "success",
        "message": "Artista creato con successo",
        "data": {
            "id_artist": artist_id,
            "name": name
        }
    }), 201


@bp.route("/<int:artist_id>", methods=["PUT"])
@token_required
@require_role("administrator")
def update_artist(artist_id):
    """Aggiorna il nome di un artista (autorizzato solo per ruolo 'administrator')."""

    artist = find_artist_by_id(artist_id)
    if not artist:
        raise NotFoundError("Artista non trovato")

    data = request.get_json()
    validate_json_payload(data, ["name"])

    updated_artist = update_artist_name(artist_id, data["name"])
    return jsonify({
        "status": "success",
        "message": "Artista aggiornato con successo",
        "data": updated_artist
    })


@bp.route("/<int:artist_id>", methods=["DELETE"])
@token_required
@require_role("administrator")
def delete_artist(artist_id):
    """Elimina un artista dal catalogo globale (autorizzato solo per ruolo 'administrator')."""

    artist = find_artist_by_id(artist_id)
    if not artist:
        raise NotFoundError("Artista non trovato")

    delete_artist_by_id(artist_id)

    # Rimuovi la foto dal bucket se nessun altro artista la usa
    image_path = dict(artist).get("image_path")
    if image_path:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM artists WHERE image_path = %s;", (image_path,))
            row = cursor.fetchone()
            count = row["total"] if row else 0
            if count == 0:
                delete_file("artists", image_path)
        finally:
            cursor.close()

    return jsonify({
        "status": "success",
        "message": "Artista eliminato con successo"
    })


@bp.route("/<int:artist_id>/image", methods=["GET"])
def get_artist_image(artist_id):
    """Serve la foto dell'artista associata."""
    artist = find_artist_by_id(artist_id)
    if not artist or not dict(artist).get("image_path"):
        raise NotFoundError("Foto dell'artista non trovata")
        
    url = get_public_url("artists", dict(artist)["image_path"])
    return redirect(url)
