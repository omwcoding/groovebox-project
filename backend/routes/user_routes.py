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
from auth import token_required
from dal.user_dal import (
    get_user_by_id,
    get_all_collectors,
    update_user_profile,
    delete_user_and_transfer_albums
)

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
        return jsonify({
            "status": "error",
            "message": "Solo i Collector possono modificare il proprio profilo"
        }), 403

    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "Nessun dato fornito"
        }), 400

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
        return jsonify({
            "status": "error",
            "message": "Nessun campo valido da aggiornare"
        }), 400

    try:
        updated_user = update_user_profile(g.current_user["id_user"], fields, values)
    except Exception as e:
        if "unique" in str(e).lower():
            return jsonify({
                "status": "error",
                "message": "Email gia' in uso"
            }), 409
        return jsonify({
            "status": "error",
            "message": "Errore durante l'aggiornamento"
        }), 500

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
        return jsonify({
            "status": "error",
            "message": "Solo i Collector possono eliminare il proprio account"
        }), 403

    user_id = g.current_user["id_user"]
    try:
        delete_user_and_transfer_albums(user_id)
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Errore durante l'eliminazione dell'account"
        }), 500

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
        return jsonify({
            "status": "error",
            "message": "Accesso riservato agli amministratori"
        }), 403

    try:
        users = get_all_collectors()
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Errore nel caricamento degli utenti"
        }), 500

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
        return jsonify({
            "status": "error",
            "message": "Accesso riservato agli amministratori"
        }), 403

    try:
        user = get_user_by_id(user_id)
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Errore nel caricamento del profilo utente"
        }), 500

    if not user or user["role"] != "collector":
        return jsonify({
            "status": "error",
            "message": "Utente non trovato"
        }), 404

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
        return jsonify({
            "status": "error",
            "message": "Accesso riservato agli amministratori"
        }), 403

    try:
        user = get_user_by_id(user_id)
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Errore interno durante il recupero dell'utente"
        }), 500

    if not user:
        return jsonify({
            "status": "error",
            "message": "Utente non trovato"
        }), 404

    if user["role"] == "administrator":
        return jsonify({
            "status": "error",
            "message": "Non e' possibile eliminare un amministratore"
        }), 403

    try:
        delete_user_and_transfer_albums(user_id)
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Errore durante l'eliminazione dell'utente"
        }), 500

    return jsonify({
        "status": "success",
        "message": "Utente eliminato con successo"
    })
