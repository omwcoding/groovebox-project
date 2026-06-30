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
from database import get_db

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

    values.append(g.current_user["id_user"])
    query = f"UPDATE USER SET {', '.join(fields)} WHERE id_user = ?"

    conn = get_db()
    try:
        conn.execute(query, values)
        conn.commit()
    except Exception as e:
        conn.close()
        if "unique" in str(e).lower():
            return jsonify({
                "status": "error",
                "message": "Email gia' in uso"
            }), 409
        return jsonify({
            "status": "error",
            "message": "Errore durante l'aggiornamento"
        }), 500

    # Recupera il profilo aggiornato
    user = conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE id_user = ?",
        (g.current_user["id_user"],)
    ).fetchone()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Profilo aggiornato con successo",
        "data": dict(user)
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
    conn = get_db()

    # Elimina prima le copie fisiche (FK) poi l'utente
    conn.execute("DELETE FROM PHYSICAL_COPY WHERE id_user = ?", (user_id,))
    conn.execute("DELETE FROM USER WHERE id_user = ?", (user_id,))
    conn.commit()
    conn.close()

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

    conn = get_db()
    users = conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE role = 'collector' ORDER BY username"
    ).fetchall()
    conn.close()

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

    conn = get_db()
    user = conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE id_user = ? AND role = 'collector'",
        (user_id,)
    ).fetchone()
    conn.close()

    if not user:
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
# Elimina anche le copie fisiche del Collector.
# --------------------------------------------------------------------------
@bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato agli amministratori"
        }), 403

    conn = get_db()
    user = conn.execute(
        "SELECT id_user, role FROM USER WHERE id_user = ?",
        (user_id,)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Utente non trovato"
        }), 404

    if user["role"] == "administrator":
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Non e' possibile eliminare un amministratore"
        }), 403

    # Elimina prima le copie fisiche (FK) poi l'utente
    conn.execute("DELETE FROM PHYSICAL_COPY WHERE id_user = ?", (user_id,))
    conn.execute("DELETE FROM USER WHERE id_user = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Utente eliminato con successo"
    })
