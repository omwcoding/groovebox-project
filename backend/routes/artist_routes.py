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

bp = Blueprint("artists", __name__, url_prefix="/api/artists")


# --------------------------------------------------------------------------
# GET /api/artists
# Restituisce tutti gli artisti (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_artists():
    try:
        artists = get_all_artists()
        return jsonify({
            "status": "success",
            "data": [dict(a) for a in artists]
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento degli artisti"}), 500


# --------------------------------------------------------------------------
# GET /api/artists/<id>
# Dettaglio di un artista con i suoi album (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["GET"])
@token_required
def get_artist(artist_id):
    try:
        artist = find_artist_by_id(artist_id)
        if not artist:
            return jsonify({
                "status": "error",
                "message": "Artista non trovato"
            }), 404

        result = dict(artist)
        albums = get_artist_albums(artist_id)
        result["albums"] = [dict(al) for al in albums]

        return jsonify({"status": "success", "data": result})
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento dell'artista"}), 500


# --------------------------------------------------------------------------
# POST /api/artists
# Crea un nuovo artista (Collector + Admin).
# Body JSON: { name }
# --------------------------------------------------------------------------
@bp.route("", methods=["POST"])
@token_required
def create_artist():
    data = request.get_json()

    if not data or not data.get("name", "").strip():
        return jsonify({
            "status": "error",
            "message": "Il campo 'name' e' obbligatorio"
        }), 400

    name = data["name"].strip()

    try:
        artist_id = insert_artist(name)
        return jsonify({
            "status": "success",
            "message": "Artista creato con successo",
            "data": {
                "id_artist": artist_id,
                "name": name
            }
        }), 201
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante la creazione dell'artista"}), 500


# --------------------------------------------------------------------------
# PUT /api/artists/<id>
# Modifica un artista (solo Admin).
# Body JSON: { name }
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["PUT"])
@token_required
def update_artist(artist_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono modificare gli artisti"
        }), 403

    try:
        artist = find_artist_by_id(artist_id)
        if not artist:
            return jsonify({
                "status": "error",
                "message": "Artista non trovato"
            }), 404

        data = request.get_json()
        if not data or not data.get("name", "").strip():
            return jsonify({
                "status": "error",
                "message": "Il campo 'name' e' obbligatorio"
            }), 400

        updated_artist = update_artist_name(artist_id, data["name"])
        return jsonify({
            "status": "success",
            "message": "Artista aggiornato con successo",
            "data": updated_artist
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante l'aggiornamento dell'artista"}), 500


# --------------------------------------------------------------------------
# DELETE /api/artists/<id>
# Elimina un artista (solo Admin).
# Rimuove anche le associazioni ALBUM_ARTIST collegate (via ON DELETE CASCADE).
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["DELETE"])
@token_required
def delete_artist(artist_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono eliminare gli artisti"
        }), 403

    try:
        artist = find_artist_by_id(artist_id)
        if not artist:
            return jsonify({
                "status": "error",
                "message": "Artista non trovato"
            }), 404

        delete_artist_by_id(artist_id)
        return jsonify({
            "status": "success",
            "message": "Artista eliminato con successo"
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante l'eliminazione dell'artista"}), 500
