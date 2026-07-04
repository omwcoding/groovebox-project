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
from dal.copy_dal import (
    get_user_copies,
    find_copy_by_id_and_user,
    insert_copy,
    create_copy_cascade,
    update_copy_data,
    delete_copy_by_id
)
from dal.album_dal import find_album_by_id

bp = Blueprint("copies", __name__, url_prefix="/api/copies")


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

    try:
        copies = get_user_copies(g.current_user["id_user"])
        return jsonify({
            "status": "success",
            "data": copies
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento della collezione"}), 500


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

    try:
        copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
        if not copy:
            return jsonify({
                "status": "error",
                "message": "Copia fisica non trovata"
            }), 404
        return jsonify({"status": "success", "data": copy})
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento della copia"}), 500


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

    try:
        # Verifica che l'album esista
        album = find_album_by_id(data["id_album"])
        if not album:
            return jsonify({
                "status": "error",
                "message": "Album di riferimento non trovato"
            }), 404

        personal_notes = data.get("personalNotes")
        if isinstance(personal_notes, str):
            personal_notes = personal_notes.strip() or None
        else:
            personal_notes = None

        copy_id = insert_copy(
            id_album=data["id_album"],
            format_val=data["format"],
            condition=data["condition"],
            personal_notes=personal_notes,
            user_id=g.current_user["id_user"]
        )

        copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
        return jsonify({
            "status": "success",
            "message": "Copia fisica aggiunta alla collezione",
            "data": copy
        }), 201
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante la creazione della copia"}), 500


# --------------------------------------------------------------------------
# POST /api/copies/cascade
# Registrazione copia a cascata (crea artista e album se non esistono).
# Body JSON: { title, artist_name, releaseYear?, genre?, format, condition, personalNotes? }
# --------------------------------------------------------------------------
@bp.route("/cascade", methods=["POST"])
@token_required
def create_copy_cascade_route():
    if g.current_user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato ai Collector"
        }), 403

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Nessun dato fornito"}), 400

    title = data.get("title", "").strip()
    artist_name = data.get("artist_name", "").strip()
    format_val = data.get("format", "").strip()
    condition = data.get("condition", "").strip()

    if not title or not artist_name or not format_val or not condition:
        return jsonify({
            "status": "error",
            "message": "I campi titolo, artista, formato e condizione sono obbligatori"
        }), 400

    release_year = data.get("releaseYear")
    if release_year:
        try:
            release_year = int(release_year)
        except ValueError:
            release_year = None
    else:
        release_year = None

    genre = data.get("genre", "").strip() or None
    personal_notes = data.get("personalNotes")
    if isinstance(personal_notes, str):
        personal_notes = personal_notes.strip() or None
    else:
        personal_notes = None

    try:
        copy_id = create_copy_cascade(
            title=title,
            artist_name=artist_name,
            release_year=release_year,
            genre=genre,
            format_val=format_val,
            condition=condition,
            personal_notes=personal_notes,
            user_id=g.current_user["id_user"]
        )
        copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
        
        return jsonify({
            "status": "success",
            "message": "Copia fisica aggiunta alla collezione con successo (creazione a cascata)",
            "data": copy
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Errore durante l'inserimento a cascata: {str(e)}"
        }), 500


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

    try:
        copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
        if not copy:
            return jsonify({
                "status": "error",
                "message": "Copia fisica non trovata"
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Nessun dato fornito"}), 400

        fields = []
        values = []
        for col in ["format", "condition", "personalNotes"]:
            if col in data:
                fields.append(f"{col} = ?")
                val = data[col]
                values.append(val.strip() if isinstance(val, str) and val else val)

        if not fields:
            return jsonify({
                "status": "error",
                "message": "Nessun campo valido da aggiornare"
            }), 400

        update_copy_data(copy_id, fields, values)
        updated_copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
        
        return jsonify({
            "status": "success",
            "message": "Copia fisica aggiornata con successo",
            "data": updated_copy
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante l'aggiornamento della copia"}), 500


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

    try:
        copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
        if not copy:
            return jsonify({
                "status": "error",
                "message": "Copia fisica non trovata"
            }), 404

        delete_copy_by_id(copy_id)
        return jsonify({
            "status": "success",
            "message": "Copia fisica eliminata dalla collezione"
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore durante l'eliminazione della copia"}), 500
