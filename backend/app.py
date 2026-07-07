"""
GrooveBox - Application Entry Point
=====================================
Configura l'applicazione Flask, registra i Blueprint e inizializza
il database al primo avvio.
"""

import os
from flask import Flask, g
from flask_cors import CORS
from dotenv import load_dotenv

from core.database import init_db, seed_db
from core.config import Config

# Carica variabili d'ambiente da .env (se presente)
load_dotenv()


def create_app():
    """Application factory: crea e configura l'istanza Flask."""
    app = Flask(__name__)

    # ---- Configurazione ----
    app.config.from_object(Config)

    # ---- CORS ----
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # TODO: restringere origins in produzione

    # ---- Inizializzazione Database ----
    init_db()
    seed_db()

    # ---- Registrazione Blueprint ----
    from routes.auth_routes import bp as auth_bp
    from routes.user_routes import bp as user_bp
    from routes.album_routes import bp as album_bp
    from routes.artist_routes import bp as artist_bp
    from routes.copy_routes import bp as copy_bp
    from routes.stats_routes import bp as stats_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(album_bp)
    app.register_blueprint(artist_bp)
    app.register_blueprint(copy_bp)
    app.register_blueprint(stats_bp)

    # ---- Rotta di health-check ----
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return {"status": "success", "message": "GrooveBox backend is running!"}

    # ---- Teardown delle connessioni al database ----
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # ---- Gestione Centralizzata Errori ----
    from core.errors import register_error_handlers
    register_error_handlers(app)

    return app


# ---------------------------------------------------------------------------
# Entry-point diretto: python app.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
