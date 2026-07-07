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

from flask import Blueprint, request, jsonify, g, current_app
from core.auth import token_required
from dal.copy_dal import (
    get_user_copies,
    find_copy_by_id_and_user,
    insert_copy,
    create_copy_cascade,
    update_copy_data,
    delete_copy_by_id,
    delete_all_copies_by_user
)
from dal.album_dal import find_album_by_id
from utils.validators import validate_json_payload
from core.errors import ForbiddenError, NotFoundError, BadRequestError

bp = Blueprint("copies", __name__, url_prefix="/api/copies")


# --------------------------------------------------------------------------
# GET /api/copies
# Restituisce tutte le copie fisiche dell'utente autenticato (solo Collector).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_my_copies():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    copies = get_user_copies(g.current_user["id_user"])
    return jsonify({
        "status": "success",
        "data": copies
    })


# --------------------------------------------------------------------------
# GET /api/copies/<id>
# Dettaglio di una singola copia (solo Collector, solo propria).
# --------------------------------------------------------------------------
@bp.route("/<int:copy_id>", methods=["GET"])
@token_required
def get_copy(copy_id):
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    if not copy:
        raise NotFoundError("Copia fisica non trovata")
        
    return jsonify({"status": "success", "data": copy})


# --------------------------------------------------------------------------
# POST /api/copies
# Aggiunge una nuova copia fisica alla collezione (solo Collector).
# Body JSON: { id_album, format, condition, personalNotes? }
# --------------------------------------------------------------------------
@bp.route("", methods=["POST"])
@token_required
def create_copy():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    data = request.get_json()
    validate_json_payload(data, ["id_album", "format", "condition"])

    # Verifica che l'album esista
    album = find_album_by_id(data["id_album"])
    if not album:
        raise NotFoundError("Album di riferimento non trovato")

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


# --------------------------------------------------------------------------
# POST /api/copies/cascade
# Registrazione copia a cascata (crea artista e album se non esistono).
# Body JSON: { title, artist_name, format, condition, releaseYear?, genre?, personalNotes? }
# --------------------------------------------------------------------------
@bp.route("/cascade", methods=["POST"])
@token_required
def create_copy_cascade_route():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    data = request.get_json()
    validate_json_payload(data, ["title", "artist_ids", "format", "condition"])

    title = data["title"].strip()
    artist_ids = data["artist_ids"]
    if not isinstance(artist_ids, list) or not artist_ids:
        raise BadRequestError("Almeno un artista deve essere associato all'album")
        
    format_val = data["format"].strip()
    condition = data["condition"].strip()

    release_year = data.get("releaseYear")
    if release_year:
        try:
            release_year = int(release_year)
        except ValueError:
            release_year = None
    else:
        release_year = None

    genre = data.get("genre", "").strip() or None
    if genre and genre not in current_app.config["ALLOWED_GENRES"]:
        raise BadRequestError(f"Genere musicale '{genre}' non valido o non consentito")

    personal_notes = data.get("personalNotes")
    if isinstance(personal_notes, str):
        personal_notes = personal_notes.strip() or None
    else:
        personal_notes = None

    copy_id = create_copy_cascade(
        title=title,
        artist_ids=artist_ids,
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


# --------------------------------------------------------------------------
# PUT /api/copies/<id>
# Modifica una propria copia fisica (solo Collector, solo propria).
# Body JSON: { format?, condition?, personalNotes? }
# --------------------------------------------------------------------------
@bp.route("/<int:copy_id>", methods=["PUT"])
@token_required
def update_copy(copy_id):
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    if not copy:
        raise NotFoundError("Copia fisica non trovata")

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    fields = []
    values = []
    for col in ["format", "condition", "personalNotes"]:
        if col in data:
            fields.append(f"{col} = ?")
            val = data[col]
            values.append(val.strip() if isinstance(val, str) and val else val)

    if not fields:
        raise BadRequestError("Nessun campo valido da aggiornare")

    update_copy_data(copy_id, fields, values)
    updated_copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    
    return jsonify({
        "status": "success",
        "message": "Copia fisica aggiornata con successo",
        "data": updated_copy
    })


# --------------------------------------------------------------------------
# DELETE /api/copies/<id>
# Elimina una propria copia fisica (solo Collector, solo propria).
# --------------------------------------------------------------------------
@bp.route("/<int:copy_id>", methods=["DELETE"])
@token_required
def delete_copy(copy_id):
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    if not copy:
        raise NotFoundError("Copia fisica non trovata")

    delete_copy_by_id(copy_id)
    return jsonify({
        "status": "success",
        "message": "Copia fisica eliminata dalla collezione"
    })


# --------------------------------------------------------------------------
# DELETE /api/copies/clear
# Elimina tutte le copie fisiche dell'utente (solo Collector).
# --------------------------------------------------------------------------
@bp.route("/clear", methods=["DELETE"])
@token_required
def clear_copies():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")

    delete_all_copies_by_user(g.current_user["id_user"])
    return jsonify({
        "status": "success",
        "message": "Tutta la collezione è stata svuotata con successo"
    })
