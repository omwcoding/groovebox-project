"""
GrooveBox - Configurazione e Connessione Database PostgreSQL (Supabase)
=============================================================================
Gestisce la connessione al database remoto PostgreSQL fornito da Supabase.
Lo schema viene creato esternamente tramite il SQL Editor di Supabase.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from werkzeug.security import generate_password_hash
from flask import g, has_app_context, current_app

try:
    from core.config import Config
except ModuleNotFoundError:
    from config import Config


def get_db():
    """
    Ritorna una connessione attiva a PostgreSQL su Supabase.
    All'interno del contesto Flask, memorizza la connessione nell'oggetto globale g.
    Utilizza RealDictCursor per abilitare l'accesso per nome colonna (chiave).
    """
    if has_app_context():
        if 'db' not in g:
            g.db = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
        return g.db
    else:
        return psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Verifica la corretta connessione al database PostgreSQL su Supabase."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        if not has_app_context() or 'db' not in g:
            conn.close()
        print(f"[OK] Connessione a Supabase PostgreSQL verificata con successo.")
    except Exception as e:
        raise RuntimeError(f"Impossibile connettersi a Supabase: {e}")


def seed_db():
    """Esegue il seeding dei dati iniziali nel database se non sono presenti record utente."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM users;")
        row = cursor.fetchone()
        count = row["total"] if row else 0
        
        if count > 0:
            print("[OK] Seed saltato: il database contiene gia' dei dati")
            return

        # Inserimento dell'amministratore di default (admin / admin)
        cursor.execute(
            """INSERT INTO users (username, name, surname, email, password_hash, role)
               VALUES (%s, %s, %s, %s, %s, %s);""",
            (
                "admin",
                "Admin",
                "GrooveBox",
                "admin@groovebox.local",
                generate_password_hash("admin"),
                "administrator"
            )
        )

        # Inserimento del collector di esempio (test / test)
        cursor.execute(
            """INSERT INTO users (username, name, surname, email, password_hash, role)
               VALUES (%s, %s, %s, %s, %s, %s);""",
            (
                "test",
                "Test",
                "Test",
                "test@test.com",
                generate_password_hash("test"),
                "collector"
            )
        )
        conn.commit()
        print("[OK] Seed completato: creati utenti admin e test")
    except Exception as e:
        conn.rollback()
        print(f"[SEED ERROR] Errore durante il seeding: {e}")
    finally:
        cursor.close()
        if not has_app_context() or 'db' not in g:
            conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
