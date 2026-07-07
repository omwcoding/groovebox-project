"""
GrooveBox - Gestione Centralizzata degli Errori
===============================================
Definisce le classi di eccezione specifiche per le risposte dell'API (HTTP 4xx/5xx)
e registra gli handler globali per catturare e formattare le risposte JSON di errore.
"""

from flask import jsonify

class APIError(Exception):
    """Eccezione base per la rappresentazione degli errori delle API."""
    def __init__(self, message, status_code=500):
        super().__init__()
        self.message = message
        self.status_code = status_code

class BadRequestError(APIError):
    """Eccezione per richieste malformate (HTTP 400)."""
    def __init__(self, message="Dati forniti non validi"):
        super().__init__(message, 400)

class UnauthorizedError(APIError):
    """Eccezione per mancata o fallita autenticazione (HTTP 401)."""
    def __init__(self, message="Non autenticato, effettua il login"):
        super().__init__(message, 401)

class ForbiddenError(APIError):
    """Eccezione per violazione dei permessi di accesso (HTTP 403)."""
    def __init__(self, message="Accesso negato: permessi insufficienti"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    """Eccezione per risorsa non trovata (HTTP 404)."""
    def __init__(self, message="Risorsa non trovata"):
        super().__init__(message, 404)

class ConflictError(APIError):
    """Eccezione per conflitti di stato (es. vincoli di unicità) (HTTP 409)."""
    def __init__(self, message="Risorsa già esistente"):
        super().__init__(message, 409)


def register_error_handlers(app):
    """Registra i gestori di errore globali a livello di applicazione Flask."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify({
            "status": "error",
            "message": error.message
        }), error.status_code

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        app.logger.error(f"Errore non gestito intercettato: {str(error)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": "Errore interno del server"
        }), 500

