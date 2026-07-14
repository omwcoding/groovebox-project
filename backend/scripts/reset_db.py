import os
import sys

# Aggiunge la cartella padre (backend/) al path di sistema per consentire l'importazione dei moduli di backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, seed_db
from scripts.seed_large import main as run_seed

def reset_database():
    print("====================================================")
    print("GrooveBox - Ripristino e Inizializzazione Database")
    print("====================================================")
    
    # Calcola il percorso del database (backend/instance/groovebox.db)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "instance", "groovebox.db")
    
    # 1. Rimuove il file del database esistente per una pulizia totale dello stato
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("[OK] Vecchio database SQLite rimosso con successo.")
        except Exception as e:
            print(f"[ERROR] Impossibile rimuovere il file del database: {e}")
            return
    else:
        print("[INFO] Nessun file di database preesistente trovato. Verrà creato da zero.")

    # 2. Inizializza il database ricreando lo schema DDL ed eseguendo il seed di base (admin e test)
    print("\n-> Inizializzazione dello schema del database e degli utenti base in corso...")
    try:
        init_db()
        seed_db()
        print("[OK] Schema del database e utenti di base inizializzati con successo.")
    except Exception as e:
        print(f"[ERROR] Errore durante l'inizializzazione del database: {e}")
        return

    # 3. Popola il database con 50 utenti, 120 album e 60 artisti arricchiti da Discogs
    print("\n-> Popolamento del database con dati reali di Discogs (Seeding)...")
    try:
        run_seed()
        print("\n[OK] Seeding completato con successo.")
    except Exception as e:
        print(f"[ERROR] Errore durante il seeding: {e}")
        return

    print("\n====================================================")
    print("[RESET COMPLETATO] Il database è ora pronto e pulito!")
    print("====================================================")

if __name__ == "__main__":
    reset_database()
