"""
GrooveBox - Route Blueprint per Autenticazione
==============================================
Fornisce gli endpoint per la registrazione dei collezionisti (Collectors)
e per il rilascio di token di sessione JWT (autenticazione).
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from dal.user_dal import insert_collector, get_user_by_username
from utils.validators import validate_json_payload
from core.errors import ConflictError, UnauthorizedError, BadRequestError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    """Registra un nuovo utente nel sistema con il ruolo di 'collector'."""
    data = request.get_json()
    validate_json_payload(data, ["username", "name", "surname", "email", "password"])

    username = data["username"].strip()
    name = data["name"].strip()
    surname = data["surname"].strip()
    email = data["email"].strip()
    password = data["password"]

    if len(password) < 6:
        raise BadRequestError("La password deve essere di almeno 6 caratteri")

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


@bp.route("/login", methods=["POST"])
def login():
    """Autentica l'utente tramite credenziali e restituisce un token di sessione JWT."""
    data = request.get_json()
    validate_json_payload(data, ["username", "password"])

    user = get_user_by_username(data["username"])

    if not user:
        raise UnauthorizedError("Credenziali non valide")

    if not check_password_hash(user["passwordHash"], data["password"]):
        raise UnauthorizedError("Credenziali non valide")

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
