"""
GrooveBox - Rotte di Autenticazione
====================================
Blueprint: /api/auth
Gestisce registrazione (solo Collector) e login con rilascio token JWT.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from database import get_db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# --------------------------------------------------------------------------
# POST /api/auth/register
# Registra un nuovo utente con ruolo 'collector'.
# --------------------------------------------------------------------------
@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validazione campi obbligatori
    required = ["username", "name", "surname", "email", "password"]
    for field in required:
        if not data or not data.get(field, "").strip():
            return jsonify({
                "status": "error",
                "message": f"Il campo '{field}' e' obbligatorio"
            }), 400

    username = data["username"].strip()
    name = data["name"].strip()
    surname = data["surname"].strip()
    email = data["email"].strip()
    password = data["password"]

    # Hash della password
    password_hash = generate_password_hash(password)

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO USER (username, name, surname, email, passwordHash, role)
               VALUES (?, ?, ?, ?, ?, 'collector')""",
            (username, name, surname, email, password_hash)
        )
        conn.commit()
        user_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]
    except Exception as e:
        conn.close()
        error_msg = str(e).lower()
        if "unique" in error_msg and "username" in error_msg:
            return jsonify({
                "status": "error",
                "message": "Username gia' in uso"
            }), 409
        if "unique" in error_msg and "email" in error_msg:
            return jsonify({
                "status": "error",
                "message": "Email gia' in uso"
            }), 409
        return jsonify({
            "status": "error",
            "message": "Errore durante la registrazione"
        }), 500
    finally:
        conn.close()

    return jsonify({
        "status": "success",
        "message": "Registrazione completata con successo",
        "data": {
            "id_user": user_id,
            "username": username
        }
    }), 201


# --------------------------------------------------------------------------
# POST /api/auth/login
# Autentica l'utente e restituisce un token JWT.
# --------------------------------------------------------------------------
@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("username") or not data.get("password"):
        return jsonify({
            "status": "error",
            "message": "Username e password sono obbligatori"
        }), 400

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM USER WHERE username = ?",
        (data["username"].strip(),)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["passwordHash"], data["password"]):
        return jsonify({
            "status": "error",
            "message": "Credenziali non valide"
        }), 401

    # Genera token JWT con scadenza a 24 ore
    token = jwt.encode(
        {
            "id_user": user["id_user"],
            "username": user["username"],
            "role": user["role"],
            "exp": datetime.datetime.now(datetime.timezone.utc)
                   + datetime.timedelta(hours=24)
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return jsonify({
        "status": "success",
        "message": "Login effettuato con successo",
        "data": {
            "token": token,
            "user": {
                "id_user": user["id_user"],
                "username": user["username"],
                "name": user["name"],
                "surname": user["surname"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    })
