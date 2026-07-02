"""
GrooveBox - Rotte Copie Fisiche
================================
Blueprint: /api/copies

Matrice di visibilita' (doc 3.4):
  Collector     -> PHYSICAL_COPY: SS scope (subset), CRUD
                   (gestisce solo le proprie copie)
  Administrator -> PHYSICAL_COPY: NONE
                   (nessun accesso alle librerie private)
"""

from flask import Blueprint, request, jsonify, g
from auth import token_required
from database import get_db
import datetime

bp = Blueprint("copies", __name__, url_prefix="/api/copies")


# --------------------------------------------------------------------------
# Helper: arricchisce un dizionario copia con la lista degli artisti dell'album
# --------------------------------------------------------------------------
def _enrich_copy_with_artists(conn, copy_dict):
    artists = conn.execute(
        """SELECT ar.id_artist, ar.name
           FROM ARTIST ar
           JOIN ALBUM_ARTIST aa ON ar.id_artist = aa.id_artist
           WHERE aa.id_album = ?
           ORDER BY ar.name""",
        (copy_dict["id_album"],)
    ).fetchall()
    copy_dict["artists"] = [dict(a) for a in artists]
    return copy_dict


# --------------------------------------------------------------------------
# GET /api/copies
# Restituisce tutte le copie fisiche dell'utente autenticato (solo Collector).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_my_copies():
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato ai Collector"
        }), 403

    conn = get_db()
    copies = conn.execute(
        """SELECT pc.*, al.title AS album_title, al.releaseYear, al.genre
           FROM PHYSICAL_COPY pc
           JOIN ALBUM al ON pc.id_album = al.id_album
           WHERE pc.id_user = ?
           ORDER BY pc.addedDate DESC""",
        (g.current_user["id_user"],)
    ).fetchall()
    
    result = []
    for c in copies:
        cd = dict(c)
        _enrich_copy_with_artists(conn, cd)
        result.append(cd)
        
    conn.close()
    return jsonify({
        "status": "success",
        "data": result
    })


# --------------------------------------------------------------------------
# GET /api/copies/<id>
# Dettaglio di una singola copia (solo Collector, solo propria).
# --------------------------------------------------------------------------
@bp.route("/<int:copy_id>", methods=["GET"])
@token_required
def get_copy(copy_id):
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato ai Collector"
        }), 403

    conn = get_db()
    copy = conn.execute(
        """SELECT pc.*, al.title AS album_title, al.releaseYear, al.genre
           FROM PHYSICAL_COPY pc
           JOIN ALBUM al ON pc.id_album = al.id_album
           WHERE pc.id_copy = ? AND pc.id_user = ?""",
        (copy_id, g.current_user["id_user"])
    ).fetchone()

    if not copy:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Copia fisica non trovata"
        }), 404

    result = _enrich_copy_with_artists(conn, dict(copy))
    conn.close()
    return jsonify({"status": "success", "data": result})


# --------------------------------------------------------------------------
# POST /api/copies
# Aggiunge una nuova copia fisica alla collezione (solo Collector).
# Body JSON: { id_album, format, condition, personalNotes? }
# --------------------------------------------------------------------------
@bp.route("", methods=["POST"])
@token_required
def create_copy():
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato ai Collector"
        }), 403

    data = request.get_json()

    # Validazione campi obbligatori
    if not data or not data.get("id_album"):
        return jsonify({
            "status": "error",
            "message": "Il campo 'id_album' e' obbligatorio"
        }), 400

    if not data.get("format", "").strip():
        return jsonify({
            "status": "error",
            "message": "Il campo 'format' e' obbligatorio"
        }), 400

    if not data.get("condition", "").strip():
        return jsonify({
            "status": "error",
            "message": "Il campo 'condition' e' obbligatorio"
        }), 400

    # Verifica che l'album esista
    conn = get_db()
    album = conn.execute(
        "SELECT id_album FROM ALBUM WHERE id_album = ?",
        (data["id_album"],)
    ).fetchone()

    if not album:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Album di riferimento non trovato"
        }), 404

    added_date = datetime.date.today().isoformat()
    personal_notes = data.get("personalNotes")
    if isinstance(personal_notes, str):
        personal_notes = personal_notes.strip() or None
    else:
        personal_notes = None

    cursor = conn.execute(
        """INSERT INTO PHYSICAL_COPY
           (format, condition, addedDate, personalNotes, id_user, id_album)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data["format"].strip(),
            data["condition"].strip(),
            added_date,
            personal_notes,
            g.current_user["id_user"],
            data["id_album"]
        )
    )
    copy_id = cursor.lastrowid
    conn.commit()

    # Recupera la copia completa
    copy = conn.execute(
        """SELECT pc.*, al.title AS album_title, al.releaseYear, al.genre
           FROM PHYSICAL_COPY pc
           JOIN ALBUM al ON pc.id_album = al.id_album
           WHERE pc.id_copy = ?""",
        (copy_id,)
    ).fetchone()
    result = _enrich_copy_with_artists(conn, dict(copy))
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Copia fisica aggiunta alla collezione",
        "data": result
    }), 201


# --------------------------------------------------------------------------
# PUT /api/copies/<id>
# Modifica una propria copia fisica (solo Collector, solo propria).
# Body JSON: { format?, condition?, personalNotes? }
# --------------------------------------------------------------------------
@bp.route("/<int:copy_id>", methods=["PUT"])
@token_required
def update_copy(copy_id):
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato ai Collector"
        }), 403

    conn = get_db()
    copy = conn.execute(
        "SELECT * FROM PHYSICAL_COPY WHERE id_copy = ? AND id_user = ?",
        (copy_id, g.current_user["id_user"])
    ).fetchone()

    if not copy:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Copia fisica non trovata"
        }), 404

    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Nessun dato fornito"
        }), 400

    fields = []
    values = []
    for col in ["format", "condition", "personalNotes"]:
        if col in data:
            fields.append(f"{col} = ?")
            val = data[col]
            values.append(val.strip() if isinstance(val, str) and val else val)

    if not fields:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Nessun campo valido da aggiornare"
        }), 400

    values.append(copy_id)
    conn.execute(
        f"UPDATE PHYSICAL_COPY SET {', '.join(fields)} WHERE id_copy = ?",
        values
    )
    conn.commit()

    # Recupera la copia aggiornata
    copy = conn.execute(
        """SELECT pc.*, al.title AS album_title, al.releaseYear, al.genre
           FROM PHYSICAL_COPY pc
           JOIN ALBUM al ON pc.id_album = al.id_album
           WHERE pc.id_copy = ?""",
        (copy_id,)
    ).fetchone()
    result = _enrich_copy_with_artists(conn, dict(copy))
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Copia fisica aggiornata con successo",
        "data": result
    })


# --------------------------------------------------------------------------
# DELETE /api/copies/<id>
# Elimina una propria copia fisica (solo Collector, solo propria).
# --------------------------------------------------------------------------
@bp.route("/<int:copy_id>", methods=["DELETE"])
@token_required
def delete_copy(copy_id):
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato ai Collector"
        }), 403

    conn = get_db()
    copy = conn.execute(
        "SELECT id_copy FROM PHYSICAL_COPY WHERE id_copy = ? AND id_user = ?",
        (copy_id, g.current_user["id_user"])
    ).fetchone()

    if not copy:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Copia fisica non trovata"
        }), 404

    conn.execute(
        "DELETE FROM PHYSICAL_COPY WHERE id_copy = ?", (copy_id,)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Copia fisica eliminata dalla collezione"
    })
