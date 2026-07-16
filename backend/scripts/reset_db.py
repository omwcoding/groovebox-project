import os
import sys

# Aggiunge la cartella padre (backend/) al path di sistema per consentire l'importazione dei moduli di backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db, init_db, seed_db
from utils.storage import clear_bucket
from scripts.seed_large import main as run_seed

def reset_database():
    print("====================================================")
    print("GrooveBox - Ripristino e Inizializzazione Database (Supabase)")
    print("====================================================")
    
    # 1. Trunca tutte le tabelle su PostgreSQL
    print("-> Svuotamento delle tabelle PostgreSQL su Supabase...")
    try:
        conn = get_db()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "TRUNCATE TABLE wishlists, discogs_cache, physical_copies, album_artists, artists, albums, users RESTART IDENTITY CASCADE;"
                )
        print("[OK] Tabelle svuotate con successo (TRUNCATE).")
    except Exception as e:
        print(f"[ERROR] Impossibile svuotare le tabelle: {e}")
        return

    # 2. Pulisce i bucket Supabase Storage
    print("\n-> Svuotamento dei bucket di Supabase Storage...")
    for bucket in ["covers", "artists", "avatars"]:
        if clear_bucket(bucket):
            print(f"[OK] Svuotato con successo il bucket storage: {bucket}")
        else:
            print(f"[WARNING] Impossibile pulire il bucket storage: {bucket}")

    # 3. Inizializza il database ricreando il seed di base (admin e test)
    print("\n-> Inizializzazione degli utenti base in corso...")
    try:
        seed_db()
        print("[OK] Utenti di base inizializzati con successo.")
    except Exception as e:
        print(f"[ERROR] Errore durante il seeding di base: {e}")
        return

    # 4. Popola il database con 50 utenti, 120 album e 60 artisti arricchiti da Discogs
    print("\n-> Popolamento del database con dati reali di Discogs (Seeding)...")
    try:
        run_seed()
        print("\n[OK] Seeding completato con successo.")
    except Exception as e:
        print(f"[ERROR] Errore durante il seeding: {e}")
        return

    print("\n====================================================")
    print("[RESET COMPLETATO] Il database Supabase è ora pronto e pulito!")
    print("====================================================")

if __name__ == "__main__":
    reset_database()
