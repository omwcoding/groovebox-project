"""
GrooveBox - Route Blueprint per Copie Fisiche
==============================================
Fornisce gli endpoint per la gestione della libreria personale di copie fisiche
dei singoli utenti (aggiunta, modifica, rimozione e svuotamento).
"""

from flask import Blueprint, request, jsonify, g, current_app
from core.auth import token_required, require_role
from dal.copy_dal import (
    get_user_copies,
    find_copy_by_id_and_user,
    insert_copy,
    update_copy_data,
    delete_copy_by_id,
    delete_all_copies_by_user
)
from dal.album_dal import find_album_by_id
from utils.validators import validate_json_payload
from core.errors import ForbiddenError, NotFoundError, BadRequestError

bp = Blueprint("copies", __name__, url_prefix="/api/copies")


@bp.route("", methods=["GET"])
@token_required
@require_role("collector")
def get_my_copies():
    """Restituisce l'elenco di tutte le copie fisiche appartenenti all'utente corrente."""

    copies = get_user_copies(g.current_user["id_user"])
    return jsonify({
        "status": "success",
        "data": copies
    })


@bp.route("/<int:copy_id>", methods=["GET"])
@token_required
@require_role("collector")
def get_copy(copy_id):
    """Restituisce il dettaglio di una singola copia fisica di proprietà dell'utente."""

    copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    if not copy:
        raise NotFoundError("Copia fisica non trovata")
        
    return jsonify({"status": "success", "data": copy})


@bp.route("", methods=["POST"])
@token_required
@require_role("collector")
def create_copy():
    """Aggiunge una nuova copia fisica alla collezione dell'utente."""

    data = request.get_json()
    validate_json_payload(data, ["id_album", "format", "condition"])

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





@bp.route("/<int:copy_id>", methods=["PUT"])
@token_required
@require_role("collector")
def update_copy(copy_id):
    """Aggiorna le informazioni relative a una copia fisica nella libreria."""

    copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    if not copy:
        raise NotFoundError("Copia fisica non trovata")

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    # Merge existing values with request data
    new_format = data.get("format", copy["format"])
    new_condition = data.get("condition", copy["condition"])
    new_notes = data.get("personalNotes") if "personalNotes" in data else copy["personalNotes"]

    if isinstance(new_format, str):
        new_format = new_format.strip()
    if isinstance(new_condition, str):
        new_condition = new_condition.strip()
    if isinstance(new_notes, str):
        new_notes = new_notes.strip() or None

    update_copy_data(copy_id, new_format, new_condition, new_notes)
    updated_copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    
    return jsonify({
        "status": "success",
        "message": "Copia fisica aggiornata con successo",
        "data": updated_copy
    })


@bp.route("/<int:copy_id>", methods=["DELETE"])
@token_required
@require_role("collector")
def delete_copy(copy_id):
    """Rimuove una copia fisica dalla collezione personale dell'utente."""

    copy = find_copy_by_id_and_user(copy_id, g.current_user["id_user"])
    if not copy:
        raise NotFoundError("Copia fisica non trovata")

    delete_copy_by_id(copy_id)
    return jsonify({
        "status": "success",
        "message": "Copia fisica eliminata dalla collezione"
    })


@bp.route("/clear", methods=["DELETE"])
@token_required
@require_role("collector")
def clear_copies():
    """Elimina l'intera collezione di copie fisiche dell'utente loggato."""

    delete_all_copies_by_user(g.current_user["id_user"])
    return jsonify({
        "status": "success",
        "message": "Tutta la collezione è stata svuotata con successo"
    })
