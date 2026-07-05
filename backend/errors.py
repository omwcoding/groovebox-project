from flask import jsonify

class APIError(Exception):
    """Eccezione base per gli errori delle nostre API"""
    def __init__(self, message, status_code=500):
        super().__init__()
        self.message = message
        self.status_code = status_code

class BadRequestError(APIError):
    def __init__(self, message="Dati forniti non validi"):
        super().__init__(message, 400)

class UnauthorizedError(APIError):
    def __init__(self, message="Non autenticato, effettua il login"):
        super().__init__(message, 401)

class ForbiddenError(APIError):
    def __init__(self, message="Accesso negato: permessi insufficienti"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    def __init__(self, message="Risorsa non trovata"):
        super().__init__(message, 404)

class ConflictError(APIError):
    def __init__(self, message="Risorsa già esistente"):
        super().__init__(message, 409)


def register_error_handlers(app):
    """Registra i gestori per gli errori globali dell'applicazione Flask."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify({
            "status": "error",
            "message": error.message
        }), error.status_code

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        # Log del server dettagliato in console per debugging
        app.logger.error(f"Errore non gestito intercettato: {str(error)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": "Errore interno del server"
        }), 500
