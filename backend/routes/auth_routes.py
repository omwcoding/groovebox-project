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
from dal.user_dal import insert_collector, get_user_by_username
from utils.validators import validate_json_payload
from errors import ConflictError, UnauthorizedError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# --------------------------------------------------------------------------
# POST /api/auth/register
# Registra un nuovo utente con ruolo 'collector'.
# --------------------------------------------------------------------------
@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    validate_json_payload(data, ["username", "name", "surname", "email", "password"])

    username = data["username"].strip()
    name = data["name"].strip()
    surname = data["surname"].strip()
    email = data["email"].strip()
    password = data["password"]

    # Hash della password
    password_hash = generate_password_hash(password)

    try:
        user_id = insert_collector(username, name, surname, email, password_hash)
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg and "username" in error_msg:
            raise ConflictError("Username gia' in uso")
        if "unique" in error_msg and "email" in error_msg:
            raise ConflictError("Email gia' in uso")
        raise e

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
    validate_json_payload(data, ["username", "password"])

    user = get_user_by_username(data["username"])

    if not user or not check_password_hash(user["passwordHash"], data["password"]):
        raise UnauthorizedError("Credenziali non valide")

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
