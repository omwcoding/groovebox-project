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

    # Configurazione Database e API Supabase
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("La variabile d'ambiente DATABASE_URL non è impostata nel file .env!")
        
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    if not SUPABASE_URL:
        raise RuntimeError("La variabile d'ambiente SUPABASE_URL non è impostata nel file .env!")
        
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    if not SUPABASE_ANON_KEY:
        raise RuntimeError("La variabile d'ambiente SUPABASE_ANON_KEY non è impostata nel file .env!")

    # Credenziali Discogs
    DISCOGS_CONSUMER_KEY = os.environ.get("DISCOGS_CONSUMER_KEY")
    DISCOGS_CONSUMER_SECRET = os.environ.get("DISCOGS_CONSUMER_SECRET")
    
    # Vincoli di validazione per il formato dei file e dei generi musicali del catalogo
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_GENRES = {
        "Rock / Alternative", "Pop", "Hip-Hop / Rap", "Electronic / Dance",
        "Ambient / Experimental", "Metal / Hard Rock", "Jazz / Blues",
        "Soul / R&B / Funk", "Reggae / Dub", "Folk / Acoustic",
        "Classical", "Soundtrack / OST", "World / Altro"
    }

    # Domini abilitati per CORS (separati da virgola, fallback per sviluppo locale)
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
