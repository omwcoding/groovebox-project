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
from core.errors import UnauthorizedError
from dal.user_dal import get_user_by_id


def token_required(f):
    """
    Decoratore per la verifica dell'autenticazione tramite JWT.
    
    Estrae il token dall'header Authorization (Bearer scheme), lo decodifica e
    verifica la presenza dell'utente a database, impostando g.current_user.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

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

