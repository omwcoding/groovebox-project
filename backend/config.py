import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Carica la chiave segreta (solleva un errore all'avvio se manca)
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("La variabile d'ambiente SECRET_KEY non è impostata nel file .env!")

    # Percorsi di base
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, "groovebox.db")
    
    # Cartelle per upload dei file
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    COVERS_FOLDER = os.path.join(UPLOAD_FOLDER, "covers")
    
    # Tipi di file copertine consentiti
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # Generi musicali ammessi sulla piattaforma
    ALLOWED_GENRES = {
        "Rock / Alternative", "Pop", "Hip-Hop / Rap", "Electronic / Dance",
        "Ambient / Experimental", "Metal / Hard Rock", "Jazz / Blues",
        "Soul / R&B / Funk", "Reggae / Dub", "Folk / Acoustic",
        "Classical", "Soundtrack / OST", "World / Altro"
    }
