"""
GrooveBox - Rotte Utenti
=========================
Blueprint: /api/users

Matrice di visibilita' (doc 3.4):
  Collector     -> USER: ONE scope, CRUD  (solo il proprio profilo)
  Administrator -> USER: ALL scope, _R_D  (legge e rimuove i Collector)
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash
from core.auth import token_required
from dal.user_dal import (
    get_user_by_id,
    get_all_collectors,
    update_user_profile,
    delete_user_and_transfer_albums
)
from core.errors import BadRequestError, ForbiddenError, NotFoundError, ConflictError

bp = Blueprint("users", __name__, url_prefix="/api/users")


# --------------------------------------------------------------------------
# GET /api/users/me
# Restituisce il profilo dell'utente autenticato (Collector + Admin).
# --------------------------------------------------------------------------
@bp.route("/me", methods=["GET"])
@token_required
def get_my_profile():
    return jsonify({
        "status": "success",
        "data": g.current_user
    })


# --------------------------------------------------------------------------
# PUT /api/users/me
# Modifica il profilo dell'utente autenticato (Collector).
# Campi aggiornabili: name, surname, email, password.
# --------------------------------------------------------------------------
@bp.route("/me", methods=["PUT"])
@token_required
def update_my_profile():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Solo i Collector possono modificare il proprio profilo")

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    # Costruisci dinamicamente la query di UPDATE
    fields = []
    values = []
    updatable = ["name", "surname", "email"]

    for field in updatable:
        if field in data and data[field] is not None:
            fields.append(f"{field} = ?")
            values.append(data[field].strip())

    # Gestione cambio password separata
    if "password" in data and data["password"]:
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


# --------------------------------------------------------------------------
# DELETE /api/users/me
# Il Collector elimina il proprio account (+ copie fisiche collegate).
# --------------------------------------------------------------------------
@bp.route("/me", methods=["DELETE"])
@token_required
def delete_my_account():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Solo i Collector possono eliminare il proprio account")

    user_id = g.current_user["id_user"]
    delete_user_and_transfer_albums(user_id)

    return jsonify({
        "status": "success",
        "message": "Account eliminato con successo"
    })


# --------------------------------------------------------------------------
# GET /api/users
# Lista tutti i Collector registrati (solo Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_all_users():
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    users = get_all_collectors()
    return jsonify({
        "status": "success",
        "data": [dict(u) for u in users]
    })


# --------------------------------------------------------------------------
# GET /api/users/<id>
# Dettaglio di un singolo Collector (solo Admin).
# --------------------------------------------------------------------------
@bp.route("/<int:user_id>", methods=["GET"])
@token_required
def get_user(user_id):
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    user = get_user_by_id(user_id)

    if not user or user["role"] != "collector":
        raise NotFoundError("Utente non trovato")

    return jsonify({
        "status": "success",
        "data": dict(user)
    })


# --------------------------------------------------------------------------
# DELETE /api/users/<id>
# Rimuove un Collector dalla piattaforma (solo Admin).
# Elimina anche le copie fisiche del Collector (via ON DELETE CASCADE).
# --------------------------------------------------------------------------
@bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    user = get_user_by_id(user_id)

    if not user:
        raise NotFoundError("Utente non trovato")

    if user["role"] == "administrator":
        raise ForbiddenError("Non e' possibile eliminare un amministratore")

    delete_user_and_transfer_albums(user_id)

    return jsonify({
        "status": "success",
        "message": "Utente eliminato con successo"
    })
