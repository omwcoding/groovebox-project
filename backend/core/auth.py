"""
GrooveBox - Middleware di Autenticazione JWT
===========================================
Fornisce il decoratore `@token_required` per proteggere le rotte dell'API.
Valida il token JWT presente nell'header HTTP Authorization e inserisce
l'utente autenticato nell'oggetto globale g.current_user.
"""

from functools import wraps
from flask import request, g, current_app
import jwt
from core.errors import UnauthorizedError, ForbiddenError
from dal.user_dal import get_user_by_id


def token_required(f):
    """
    Decoratore per la verifica dell'autenticazione tramite JWT.
    
    Estrae il token dal cookie 'token' o dall'header Authorization, lo decodifica e
    verifica la presenza dell'utente a database, impostando g.current_user.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            raise UnauthorizedError("Token di autenticazione mancante")

        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token scaduto, effettua nuovamente il login")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Token non valido")

        user = get_user_by_id(payload["id_user"])

        if not user:
            raise UnauthorizedError("Utente associato al token non trovato")

        g.current_user = dict(user)
        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    """
    Decoratore per limitare l'accesso alle rotte in base al ruolo dell'utente.
    Deve essere applicato sotto (dopo) @token_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "current_user") or g.current_user is None:
                raise UnauthorizedError("Autenticazione richiesta")

            user_role = g.current_user.get("role")
            if user_role not in roles:
                raise ForbiddenError("Accesso non consentito per questo ruolo")

            return f(*args, **kwargs)
        return decorated
    return decorator

