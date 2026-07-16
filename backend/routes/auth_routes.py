"""
Mint - Route Blueprint per Autenticazione
==============================================
Fornisce gli endpoint per la registrazione dei collezionisti (Collectors)
e per il rilascio di token di sessione JWT (autenticazione) tramite Supabase Storage.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from dal.user_dal import insert_collector, get_user_by_username, update_user_profile
from utils.validators import validate_json_payload
from utils.storage import upload_file, delete_file
from core.errors import ConflictError, UnauthorizedError, BadRequestError
import uuid

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    """Registra un nuovo utente nel sistema con il ruolo di 'collector'."""
    avatar_file = None
    if request.content_type and "multipart/form-data" in request.content_type:
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        surname = request.form.get("surname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        avatar_file = request.files.get("avatar")
    else:
        data = request.get_json()
        validate_json_payload(data, ["username", "name", "surname", "email", "password"])
        username = data["username"].strip()
        name = data["name"].strip()
        surname = data["surname"].strip()
        email = data["email"].strip()
        password = data["password"]

    if not username or not name or not surname or not email or not password:
        raise BadRequestError("Tutti i campi sono obbligatori")

    if len(password) < 6:
        raise BadRequestError("La password deve essere di almeno 6 caratteri")

    password_hash = generate_password_hash(password)

    avatar_filename = None
    if avatar_file:
        from werkzeug.utils import secure_filename
        safe_original = secure_filename(avatar_file.filename)
        if safe_original and "." in safe_original:
            ext = safe_original.rsplit(".", 1)[1].lower()
            if ext in current_app.config["ALLOWED_EXTENSIONS"]:
                avatar_filename = f"avatar_reg_{uuid.uuid4().hex[:8]}.{ext}"
                file_bytes = avatar_file.read()
                if not upload_file("avatars", avatar_filename, file_bytes, avatar_file.mimetype):
                    raise BadRequestError("Errore nel caricamento dell'avatar su Supabase Storage")

    try:
        user_id = insert_collector(username, name, surname, email, password_hash)
        if avatar_filename:
            update_user_profile(user_id, ["avatar_path = %s"], [avatar_filename])
    except Exception as e:
        # Rimuovi il file se l'inserimento nel database fallisce
        if avatar_filename:
            try:
                delete_file("avatars", avatar_filename)
            except Exception:
                pass
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

    if not check_password_hash(user["password_hash"], data["password"]):
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

    response = jsonify({
        "status": "success",
        "message": "Login effettuato con successo",
        "data": {
            "user": {
                "id_user": user["id_user"],
                "username": user["username"],
                "name": user["name"],
                "surname": user["surname"],
                "email": user["email"],
                "role": user["role"],
                "is_public": user["is_public"],
                "bio": user["bio"],
                "avatar_path": user["avatar_path"]
            }
        }
    })
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=False,  # False per sviluppo locale su http
        samesite="Lax",
        max_age=24 * 3600
    )
    return response


@bp.route("/logout", methods=["POST"])
def logout():
    """Effettua il logout dell'utente eliminando il cookie di sessione."""
    response = jsonify({
        "status": "success",
        "message": "Logout effettuato con successo"
    })
    response.delete_cookie("token", samesite="Lax")
    return response
