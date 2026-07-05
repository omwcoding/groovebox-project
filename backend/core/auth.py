"""
GrooveBox - Middleware di autenticazione JWT
============================================
Decoratore @token_required per la protezione delle rotte API.
Estrae il token JWT dall'header Authorization, lo valida e rende
disponibile l'utente corrente in flask.g.current_user.
"""

from functools import wraps
from flask import request, g, current_app
import jwt
try:
    from core.errors import UnauthorizedError
except ModuleNotFoundError:
    from errors import UnauthorizedError
from dal.user_dal import get_user_by_id


def token_required(f):
    """Decoratore: richiede un token JWT valido nell'header Authorization.

    In caso di successo, popola `g.current_user` con il dizionario
    completo dell'utente (escluso passwordHash) e prosegue verso
    la funzione decorata.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Estrai il token dall'header "Authorization: Bearer <token>"
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

        # Verifica che l'utente esista ancora nel database
        user = get_user_by_id(payload["id_user"])

        if not user:
            raise UnauthorizedError("Utente associato al token non trovato")

        g.current_user = dict(user)
        return f(*args, **kwargs)

    return decorated
