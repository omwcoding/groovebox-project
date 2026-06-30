"""
GrooveBox - Middleware di autenticazione JWT
============================================
Decoratore @token_required per la protezione delle rotte API.
Estrae il token JWT dall'header Authorization, lo valida e rende
disponibile l'utente corrente in flask.g.current_user.
"""

from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from database import get_db


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
            return jsonify({
                "status": "error",
                "message": "Token di autenticazione mancante"
            }), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": "error",
                "message": "Token scaduto, effettua nuovamente il login"
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "status": "error",
                "message": "Token non valido"
            }), 401

        # Verifica che l'utente esista ancora nel database
        conn = get_db()
        user = conn.execute(
            "SELECT id_user, username, name, surname, email, role "
            "FROM USER WHERE id_user = ?",
            (payload["id_user"],)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({
                "status": "error",
                "message": "Utente associato al token non trovato"
            }), 401

        g.current_user = dict(user)
        return f(*args, **kwargs)

    return decorated
