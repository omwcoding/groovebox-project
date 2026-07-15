"""
GrooveBox - Route Blueprint per Utenti
======================================
Definisce le rotte per la consultazione e modifica del proprio profilo (Collector)
e per le operazioni di moderazione sui Collector da parte degli amministratori.
"""

from flask import Blueprint, request, jsonify, g, send_from_directory, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from core.auth import token_required, require_role
from core.database import get_db
from dal.user_dal import (
    get_user_by_id,
    get_all_collectors,
    update_user_profile,
    delete_user_and_keep_albums,
    get_user_public_profile
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
@require_role("collector")
def update_my_profile():
    """Consente all'utente (solo Collector) di aggiornare i propri dati anagrafici o la password."""

    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito nella richiesta")

    fields = []
    values = []
    updatable = ["name", "surname"]

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
@require_role("collector")
def delete_my_account():
    """Consente ad un Collector di eliminare permanentemente il proprio account."""

    user_id = g.current_user["id_user"]
    delete_user_and_keep_albums(user_id)

    return jsonify({
        "status": "success",
        "message": "Account eliminato con successo"
    })


@bp.route("", methods=["GET"])
@token_required
@require_role("administrator")
def get_all_users():
    """Restituisce l'elenco completo di tutti i Collector registrati (solo Admin)."""

    users = get_all_collectors()
    return jsonify({
        "status": "success",
        "data": [dict(u) for u in users]
    })


@bp.route("/<int:user_id>", methods=["GET"])
@token_required
@require_role("administrator")
def get_user(user_id):
    """Restituisce i dettagli anagrafici e le metriche di un singolo Collector (solo Admin)."""

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
@require_role("administrator")
def delete_user(user_id):
    """Elimina definitivamente un Collector dalla piattaforma (solo Admin)."""

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
    """Restituisce il profilo pubblico e le copie fisiche (Vault) di un utente tramite username.
    Accessibile solo se l'utente ha abilitato is_public = 1. Risponde 404 in entrambi
    i casi (non trovato / profilo privato) per non rivelare l'esistenza dell'account.
    """
    user_row = get_user_public_profile(username)
    
    if not user_row:
        raise NotFoundError("Profilo non trovato o non pubblico")
        
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


@bp.route("/me/public-profile", methods=["PUT"])
@token_required
@require_role("collector")
def update_public_profile():
    """Aggiorna le impostazioni del profilo pubblico: toggle is_public e bio.
    Riservato ai Collector."""

    data = request.get_json()
    if data is None:
        raise BadRequestError("Nessun dato fornito")

    fields = []
    values = []

    if "is_public" in data:
        fields.append("is_public = ?")
        values.append(1 if data["is_public"] else 0)

    if "bio" in data:
        bio = data["bio"]
        if bio is not None:
            bio = bio.strip()[:500] or None  # max 500 caratteri
        fields.append("bio = ?")
        values.append(bio)

    if not fields:
        raise BadRequestError("Nessun campo valido da aggiornare")

    updated_user = update_user_profile(g.current_user["id_user"], fields, values)
    authUser = dict(updated_user)

    return jsonify({
        "status": "success",
        "message": "Impostazioni profilo pubblico aggiornate",
        "data": authUser
    })


@bp.route("/me/avatar", methods=["POST"])
@token_required
def upload_avatar():
    """Carica o sostituisce la foto profilo (avatar) dell'utente autenticato."""
    if "file" not in request.files:
        raise BadRequestError("Nessun file fornito nella richiesta")

    file = request.files["file"]
    if not file or not file.filename:
        raise BadRequestError("File non valido")

    from werkzeug.utils import secure_filename
    import os
    import uuid

    safe_original = secure_filename(file.filename)
    if not safe_original or "." not in safe_original:
        raise BadRequestError("Nome file non supportato")

    ext = safe_original.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        raise BadRequestError("Formato immagine non supportato (ammessi: jpg, png, webp)")

    upload_dir = current_app.config["AVATARS_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"avatar_{g.current_user['id_user']}_{uuid.uuid4().hex[:8]}.{ext}"
    file.save(os.path.join(upload_dir, filename))

    # Elimina il vecchio avatar se presente
    old_avatar = g.current_user.get("avatar_path")
    if old_avatar:
        try:
            os.remove(os.path.join(upload_dir, old_avatar))
        except Exception:
            pass

    updated_user = update_user_profile(g.current_user["id_user"], ["avatar_path = ?"], [filename])
    return jsonify({
        "status": "success",
        "message": "Foto profilo aggiornata con successo",
        "data": dict(updated_user)
    }), 200


@bp.route("/<int:user_id>/avatar", methods=["GET"])
def get_avatar(user_id):
    """Restituisce il file immagine dell'avatar dell'utente specificato."""
    user = get_user_by_id(user_id)
    if not user or not user["avatar_path"]:
        raise NotFoundError("Avatar non trovato")

    upload_dir = current_app.config["AVATARS_FOLDER"]
    return send_from_directory(upload_dir, user["avatar_path"])

