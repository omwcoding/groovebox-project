"""
GrooveBox - Configurazione Globale dell'Applicazione
===================================================
Definisce le impostazioni ambientali, le chiavi di cifratura, i percorsi delle 
directory di sistema e i vincoli di validazione relativi ai file e ai metadati 
del catalogo musicale.
"""

import os
from dotenv import load_dotenv

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CORE_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))

class Config:
    """Classe contenitrice delle costanti di configurazione applicativa."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("La variabile d'ambiente SECRET_KEY non è impostata nel file .env!")

    DATABASE_PATH = os.path.join(BACKEND_DIR, "instance", "groovebox.db")
    
    # Percorsi per la memorizzazione degli upload fisici (es. copertine degli album)
    UPLOAD_FOLDER = os.path.join(BACKEND_DIR, "uploads")
    COVERS_FOLDER = os.path.join(UPLOAD_FOLDER, "covers")
    
    # Vincoli di validazione per il formato dei file e dei generi musicali del catalogo
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_GENRES = {
        "Rock / Alternative", "Pop", "Hip-Hop / Rap", "Electronic / Dance",
        "Ambient / Experimental", "Metal / Hard Rock", "Jazz / Blues",
        "Soul / R&B / Funk", "Reggae / Dub", "Folk / Acoustic",
        "Classical", "Soundtrack / OST", "World / Altro"
    }
