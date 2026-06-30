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
from database import get_db

bp = Blueprint("artists", __name__, url_prefix="/api/artists")


# --------------------------------------------------------------------------
# GET /api/artists
# Restituisce tutti gli artisti (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_artists():
    conn = get_db()
    artists = conn.execute(
        "SELECT * FROM ARTIST ORDER BY name"
    ).fetchall()
    conn.close()

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
    conn = get_db()
    artist = conn.execute(
        "SELECT * FROM ARTIST WHERE id_artist = ?", (artist_id,)
    ).fetchone()

    if not artist:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Artista non trovato"
        }), 404

    result = dict(artist)

    # Includi gli album associati
    albums = conn.execute(
        """SELECT al.id_album, al.title, al.releaseYear, al.genre
           FROM ALBUM al
           JOIN ALBUM_ARTIST aa ON al.id_album = aa.id_album
           WHERE aa.id_artist = ?
           ORDER BY al.releaseYear""",
        (artist_id,)
    ).fetchall()
    conn.close()

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

    if not data or not data.get("name", "").strip():
        return jsonify({
            "status": "error",
            "message": "Il campo 'name' e' obbligatorio"
        }), 400

    name = data["name"].strip()

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO ARTIST (name) VALUES (?)", (name,)
    )
    artist_id = cursor.lastrowid
    conn.commit()
    conn.close()

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
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono modificare gli artisti"
        }), 403

    conn = get_db()
    artist = conn.execute(
        "SELECT * FROM ARTIST WHERE id_artist = ?", (artist_id,)
    ).fetchone()

    if not artist:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Artista non trovato"
        }), 404

    data = request.get_json()
    if not data or not data.get("name", "").strip():
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Il campo 'name' e' obbligatorio"
        }), 400

    conn.execute(
        "UPDATE ARTIST SET name = ? WHERE id_artist = ?",
        (data["name"].strip(), artist_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Artista aggiornato con successo",
        "data": {
            "id_artist": artist_id,
            "name": data["name"].strip()
        }
    })


# --------------------------------------------------------------------------
# DELETE /api/artists/<id>
# Elimina un artista (solo Admin).
# Rimuove anche le associazioni ALBUM_ARTIST collegate.
# --------------------------------------------------------------------------
@bp.route("/<int:artist_id>", methods=["DELETE"])
@token_required
def delete_artist(artist_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono eliminare gli artisti"
        }), 403

    conn = get_db()
    artist = conn.execute(
        "SELECT id_artist FROM ARTIST WHERE id_artist = ?", (artist_id,)
    ).fetchone()

    if not artist:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Artista non trovato"
        }), 404

    # Eliminazione a cascata manuale
    conn.execute("DELETE FROM ALBUM_ARTIST WHERE id_artist = ?", (artist_id,))
    conn.execute("DELETE FROM ARTIST WHERE id_artist = ?", (artist_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Artista eliminato con successo"
    })
