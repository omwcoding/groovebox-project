"""
GrooveBox - Route Blueprint per Utenti
======================================
Definisce le rotte per la consultazione e modifica del proprio profilo (Collector)
e per le operazioni di moderazione sui Collector da parte degli amministratori.
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from core.auth import token_required
from core.database import get_db
from dal.user_dal import (
    get_user_by_id,
    get_all_collectors,
    update_user_profile,
    delete_user_and_keep_albums
)
from core.errors import BadRequestError, ForbiddenError, NotFoundError, ConflictError

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.route("/me", methods=["GET"])
@token_required
def get_my_profile():
    """Restituisce il profilo dell'utente correntemente autenticato."""
    return jsonify({
        "status": "success",
        "data": g.current_user
    })


@bp.route("/me", methods=["PUT"])
@token_required
def update_my_profile():
    """Consente all'utente (solo Collector) di aggiornare i propri dati anagrafici o la password."""
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Solo i Collector possono modificare il proprio profilo")

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    fields = []
    values = []
    updatable = ["name", "surname", "email"]

    for field in updatable:
        if field in data and data[field] is not None:
            fields.append(f"{field} = ?")
            values.append(data[field].strip())

    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            raise BadRequestError("La nuova password deve essere di almeno 6 caratteri")
            
        current_password = data.get("current_password")
        if not current_password:
            raise BadRequestError("La password attuale è obbligatoria per effettuare la modifica")
            
        conn = get_db()
        db_user = conn.execute("SELECT passwordHash FROM USER WHERE id_user = ?", (g.current_user["id_user"],)).fetchone()
        
        if not db_user or not check_password_hash(db_user["passwordHash"], current_password):
            raise BadRequestError("La password attuale inserita non è corretta")
            
        fields.append("passwordHash = ?")
        values.append(generate_password_hash(data["password"]))

    if not fields:
        raise BadRequestError("Nessun campo valido da aggiornare")

    try:
        updated_user = update_user_profile(g.current_user["id_user"], fields, values)
    except Exception as e:
        if "unique" in str(e).lower():
            raise ConflictError("Email gia' in uso")
        raise e

    return jsonify({
        "status": "success",
        "message": "Profilo aggiornato con successo",
        "data": dict(updated_user)
    })


@bp.route("/me", methods=["DELETE"])
@token_required
def delete_my_account():
    """Consente ad un Collector di eliminare permanentemente il proprio account."""
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Solo i Collector possono eliminare il proprio account")

    user_id = g.current_user["id_user"]
    delete_user_and_keep_albums(user_id)

    return jsonify({
        "status": "success",
        "message": "Account eliminato con successo"
    })


@bp.route("", methods=["GET"])
@token_required
def get_all_users():
    """Restituisce l'elenco completo di tutti i Collector registrati (solo Admin)."""
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    users = get_all_collectors()
    return jsonify({
        "status": "success",
        "data": [dict(u) for u in users]
    })


@bp.route("/<int:user_id>", methods=["GET"])
@token_required
def get_user(user_id):
    """Restituisce i dettagli anagrafici e le metriche di un singolo Collector (solo Admin)."""
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    user = get_user_by_id(user_id)

    if not user or user["role"] != "collector":
        raise NotFoundError("Utente non trovato")

    conn = get_db()
    copies_count = conn.execute("SELECT COUNT(*) FROM PHYSICAL_COPY WHERE id_user = ?", (user_id,)).fetchone()[0]
    albums_count = conn.execute("SELECT COUNT(*) FROM ALBUM WHERE id_user = ?", (user_id,)).fetchone()[0]

    user_dict = dict(user)
    user_dict["copies_count"] = copies_count
    user_dict["albums_count"] = albums_count

    return jsonify({
        "status": "success",
        "data": user_dict
    })


@bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    """Elimina definitivamente un Collector dalla piattaforma (solo Admin)."""
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    user = get_user_by_id(user_id)

    if not user:
        raise NotFoundError("Utente non trovato")

    if user["role"] == "administrator":
        raise ForbiddenError("Non e' possibile eliminare un amministratore")

    delete_user_and_keep_albums(user_id)

    return jsonify({
        "status": "success",
        "message": "Utente eliminato con successo"
    })

@bp.route("/share/<username>", methods=["GET"])
def get_shared_profile(username):
    """Restituisce il profilo pubblico e le copie fisiche (Vault) di un utente tramite username."""
    conn = get_db()
    user_row = conn.execute(
        "SELECT id_user, username, name, surname FROM USER WHERE username = ? AND role = 'collector'",
        (username,)
    ).fetchone()
    
    if not user_row:
        raise NotFoundError("Utente o profilo condiviso non trovato")
        
    user_data = dict(user_row)
    
    from dal.copy_dal import get_user_copies
    copies = get_user_copies(user_data["id_user"])
    
    return jsonify({
        "status": "success",
        "data": {
            "user": user_data,
            "copies": copies
        }
    })
