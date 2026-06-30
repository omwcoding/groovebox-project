"""
GrooveBox - Rotte Album
========================
Blueprint: /api/albums

Matrice di visibilita' (doc 3.4):
  Collector     -> ALBUM: ALL scope, CR__  (crea e consulta)
  Administrator -> ALBUM: ALL scope, CRUD  (gestione completa catalogo)

Gestisce anche la relazione PUBLISHES (ALBUM_ARTIST) in modo trasparente:
  - In lettura: ogni album include la lista dei suoi artisti.
  - In scrittura: accetta un array artist_ids per creare le associazioni.
"""

from flask import Blueprint, request, jsonify, g
from auth import token_required
from database import get_db

bp = Blueprint("albums", __name__, url_prefix="/api/albums")


# --------------------------------------------------------------------------
# Helper: arricchisce un dizionario album con la lista dei suoi artisti
# --------------------------------------------------------------------------
def _enrich_album_with_artists(conn, album_dict):
    """Aggiunge la chiave 'artists' (lista) al dizionario dell'album."""
    artists = conn.execute(
        """SELECT ar.id_artist, ar.name
           FROM ARTIST ar
           JOIN ALBUM_ARTIST aa ON ar.id_artist = aa.id_artist
           WHERE aa.id_album = ?
           ORDER BY ar.name""",
        (album_dict["id_album"],)
    ).fetchall()
    album_dict["artists"] = [dict(a) for a in artists]
    return album_dict


# --------------------------------------------------------------------------
# GET /api/albums
# Restituisce tutti gli album del catalogo (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_albums():
    conn = get_db()
    albums = conn.execute(
        "SELECT * FROM ALBUM ORDER BY title"
    ).fetchall()

    result = []
    for album in albums:
        a = dict(album)
        _enrich_album_with_artists(conn, a)
        result.append(a)

    conn.close()
    return jsonify({"status": "success", "data": result})


# --------------------------------------------------------------------------
# GET /api/albums/<id>
# Dettaglio di un singolo album (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["GET"])
@token_required
def get_album(album_id):
    conn = get_db()
    album = conn.execute(
        "SELECT * FROM ALBUM WHERE id_album = ?", (album_id,)
    ).fetchone()

    if not album:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Album non trovato"
        }), 404

    result = _enrich_album_with_artists(conn, dict(album))
    conn.close()
    return jsonify({"status": "success", "data": result})


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

    conn = get_db()

    # Verifica che gli artist_ids esistano
    for aid in artist_ids:
        artist = conn.execute(
            "SELECT id_artist FROM ARTIST WHERE id_artist = ?", (aid,)
        ).fetchone()
        if not artist:
            conn.close()
            return jsonify({
                "status": "error",
                "message": f"Artista con id {aid} non trovato"
            }), 404

    # Inserimento album
    cursor = conn.execute(
        """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user)
           VALUES (?, ?, ?, NULL, ?)""",
        (title, release_year, genre, g.current_user["id_user"])
    )
    album_id = cursor.lastrowid

    # Creazione associazioni ALBUM_ARTIST
    for aid in artist_ids:
        conn.execute(
            "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
            (album_id, aid)
        )

    conn.commit()

    # Recupera l'album completo per la risposta
    album = conn.execute(
        "SELECT * FROM ALBUM WHERE id_album = ?", (album_id,)
    ).fetchone()
    result = _enrich_album_with_artists(conn, dict(album))
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Album inserito nel catalogo con successo",
        "data": result
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
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono modificare gli album"
        }), 403

    conn = get_db()
    album = conn.execute(
        "SELECT * FROM ALBUM WHERE id_album = ?", (album_id,)
    ).fetchone()

    if not album:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Album non trovato"
        }), 404

    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Nessun dato fornito"
        }), 400

    # Aggiornamento campi
    fields = []
    values = []
    for col in ["title", "releaseYear", "genre"]:
        if col in data:
            fields.append(f"{col} = ?")
            val = data[col]
            values.append(val.strip() if isinstance(val, str) else val)

    if fields:
        values.append(album_id)
        conn.execute(
            f"UPDATE ALBUM SET {', '.join(fields)} WHERE id_album = ?",
            values
        )

    # Aggiornamento associazioni artisti (se forniti)
    if "artist_ids" in data:
        # Verifica esistenza artisti
        for aid in data["artist_ids"]:
            a = conn.execute(
                "SELECT id_artist FROM ARTIST WHERE id_artist = ?", (aid,)
            ).fetchone()
            if not a:
                conn.close()
                return jsonify({
                    "status": "error",
                    "message": f"Artista con id {aid} non trovato"
                }), 404

        # Ricrea le associazioni
        conn.execute(
            "DELETE FROM ALBUM_ARTIST WHERE id_album = ?", (album_id,)
        )
        for aid in data["artist_ids"]:
            conn.execute(
                "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                (album_id, aid)
            )

    conn.commit()

    # Recupera album aggiornato
    album = conn.execute(
        "SELECT * FROM ALBUM WHERE id_album = ?", (album_id,)
    ).fetchone()
    result = _enrich_album_with_artists(conn, dict(album))
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Album aggiornato con successo",
        "data": result
    })


# --------------------------------------------------------------------------
# DELETE /api/albums/<id>
# Elimina un album dal catalogo (solo Admin).
# Rimuove anche le associazioni ALBUM_ARTIST e le PHYSICAL_COPY collegate.
# --------------------------------------------------------------------------
@bp.route("/<int:album_id>", methods=["DELETE"])
@token_required
def delete_album(album_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Solo gli amministratori possono eliminare gli album"
        }), 403

    conn = get_db()
    album = conn.execute(
        "SELECT id_album FROM ALBUM WHERE id_album = ?", (album_id,)
    ).fetchone()

    if not album:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Album non trovato"
        }), 404

    # Eliminazione a cascata manuale (FK senza ON DELETE CASCADE)
    conn.execute("DELETE FROM ALBUM_ARTIST WHERE id_album = ?", (album_id,))
    conn.execute("DELETE FROM PHYSICAL_COPY WHERE id_album = ?", (album_id,))
    conn.execute("DELETE FROM ALBUM WHERE id_album = ?", (album_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Album eliminato dal catalogo con successo"
    })
