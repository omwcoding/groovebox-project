"""
GrooveBox - Rotte Artisti
==========================
Blueprint: /api/artists

Matrice di visibilita' (doc 3.4):
  Collector     -> ARTIST: ALL scope, CR__  (crea e consulta)
  Administrator -> ARTIST: ALL scope, CRUD  (gestione completa)
"""

from flask import Blueprint, request, jsonify, g
from auth import token_required
from dal.artist_dal import (
    get_all_artists,
    find_artist_by_id,
    get_artist_albums,
    insert_artist,
    update_artist_name,
    delete_artist_by_id
)
from utils.validators import validate_json_payload
from errors import ForbiddenError, NotFoundError

bp = Blueprint("artists", __name__, url_prefix="/api/artists")


# --------------------------------------------------------------------------
# GET /api/artists
# Restituisce tutti gli artisti (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_artists():
    artists = get_all_artists()
    return jsonify({
        "status": "success",
        "data": [dict(a) for a in artists]
    })


# --------------------------------------------------------------------------
# GET /api/artists/<id>
# Dettaglio di un artista con i suoi album (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["GET"])
@token_required
def get_artist(artist_id):
    artist = find_artist_by_id(artist_id)
    if not artist:
        raise NotFoundError("Artista non trovato")

    result = dict(artist)
    albums = get_artist_albums(artist_id)
    result["albums"] = [dict(al) for al in albums]

    return jsonify({"status": "success", "data": result})


# --------------------------------------------------------------------------
# POST /api/artists
# Crea un nuovo artista (Collector + Admin).
# Body JSON: { name }
# --------------------------------------------------------------------------
@bp.route("", methods=["POST"])
@token_required
def create_artist():
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


# --------------------------------------------------------------------------
# PUT /api/artists/<id>
# Modifica un artista (solo Admin).
# Body JSON: { name }
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["PUT"])
@token_required
def update_artist(artist_id):
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Solo gli amministratori possono modificare gli artisti")

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


# --------------------------------------------------------------------------
# DELETE /api/artists/<id>
# Elimina un artista (solo Admin).
# Rimuove anche le associazioni ALBUM_ARTIST collegate (via ON DELETE CASCADE).
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["DELETE"])
@token_required
def delete_artist(artist_id):
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Solo gli amministratori possono eliminare gli artisti")

    artist = find_artist_by_id(artist_id)
    if not artist:
        raise NotFoundError("Artista non trovato")

    delete_artist_by_id(artist_id)
    return jsonify({
        "status": "success",
        "message": "Artista eliminato con successo"
    })
