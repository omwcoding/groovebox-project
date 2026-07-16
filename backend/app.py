"""
GrooveBox - Punto di Ingresso dell'Applicazione
==============================================
Inizializza l'istanza Flask, configura il middleware CORS, registra i blueprint 
per le rotte API, gestisce il ciclo di vita del database SQLite e attiva il 
gestore centralizzato delle eccezioni.
"""

from flask import Flask, g
from flask_cors import CORS
from dotenv import load_dotenv
import os

from core.database import init_db, seed_db
from core.config import Config

load_dotenv()


def create_app():
    """Application Factory per la configurazione e creazione dell'istanza Flask."""
    app = Flask(__name__)

    app.config.from_object(Config)

    # Abilitazione delle chiamate Cross-Origin Resource Sharing per le rotte API
    CORS(app, resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGINS"]}}, supports_credentials=True)

    # Bootstrap e seeding dei dati iniziali del database
    init_db()
    seed_db()



    from routes.auth_routes import bp as auth_bp
    from routes.user_routes import bp as user_bp
    from routes.album_routes import bp as album_bp
    from routes.artist_routes import bp as artist_bp
    from routes.copy_routes import bp as copy_bp
    from routes.stats_routes import bp as stats_bp
    from routes.discogs_routes import bp as discogs_bp
    from routes.wishlist_routes import bp as wishlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(album_bp)
    app.register_blueprint(artist_bp)
    app.register_blueprint(copy_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(discogs_bp)
    app.register_blueprint(wishlist_bp)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Verifica lo stato di operatività del backend."""
        return {"status": "success", "message": "Mint backend is running!"}

    @app.teardown_appcontext
    def close_db(error):
        """Rilascia la connessione al database associata al contesto dell'applicazione."""
        db = g.pop('db', None)
        if db is not None:
            db.close()

    from core.errors import register_error_handlers
    register_error_handlers(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
