"""
GrooveBox - Configurazione e Connessione Database Relazionale
=============================================================
Definisce lo schema DDL delle tabelle relazionali dell'applicazione 
(USER, ALBUM, ARTIST, ALBUM_ARTIST, PHYSICAL_COPY) aderendo al modello logico, 
e fornisce l'infrastruttura di bootstrap del database SQLite.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from flask import g, has_app_context

try:
    from core.config import Config
except ModuleNotFoundError:
    from config import Config


def get_db():
    """
    Ritorna una connessione attiva a SQLite garantendo l'abilitazione delle 
    foreign key e la configurazione del row factory per l'accesso per chiave.
    All'interno del contesto Flask, memorizza la connessione nell'oggetto globale g.
    """
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(Config.DATABASE_PATH)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db
    else:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


# Schema DDL del database relazionale (Capitolo 3.2 del documento di progetto)
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS USER (
    id_user         INTEGER     PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(30)     NOT NULL UNIQUE,
    name            VARCHAR(50)     NOT NULL,
    surname         VARCHAR(50)     NOT NULL,
    email           VARCHAR(100)    NOT NULL UNIQUE,
    passwordHash    VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'collector'
                                    CHECK (role IN ('collector', 'administrator'))
);

CREATE TABLE IF NOT EXISTS ALBUM (
    id_album        INTEGER     PRIMARY KEY AUTOINCREMENT,
    title           VARCHAR(100)    NOT NULL,
    releaseYear     INTEGER,
    genre           VARCHAR(100),
    coverPath       VARCHAR(255),
    id_user         INTEGER         DEFAULT NULL,
    discogs_id      INTEGER         UNIQUE,
    tracklist       TEXT,
    label           VARCHAR(100),
    catno           VARCHAR(50),
    barcode         VARCHAR(50),
    country         VARCHAR(50),

    FOREIGN KEY (id_user) REFERENCES USER(id_user) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ARTIST (
    id_artist       INTEGER     PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)    NOT NULL,
    discogs_id      INTEGER         UNIQUE,
    biography       TEXT,
    image_path      VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS ALBUM_ARTIST (
    id_album        INTEGER     NOT NULL,
    id_artist       INTEGER     NOT NULL,

    PRIMARY KEY (id_album, id_artist),
    FOREIGN KEY (id_album)  REFERENCES ALBUM(id_album) ON DELETE CASCADE,
    FOREIGN KEY (id_artist) REFERENCES ARTIST(id_artist) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PHYSICAL_COPY (
    id_copy         INTEGER     PRIMARY KEY AUTOINCREMENT,
    format          VARCHAR(20)     NOT NULL CHECK (format IN ('Vinile', 'CD', 'Cassetta')),
    condition       VARCHAR(50)     NOT NULL CHECK (condition IN ('Nuovo', 'Come nuovo', 'Buono', 'Discreto', 'Rovinato')),
    addedDate       DATE            NOT NULL,
    personalNotes   TEXT,
    id_user         INTEGER         NOT NULL,
    id_album        INTEGER         NOT NULL,

    FOREIGN KEY (id_user)  REFERENCES USER(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_album) REFERENCES ALBUM(id_album) ON DELETE CASCADE
);
"""


def init_db():
    """Inizializza il file del database SQLite applicando lo schema DDL."""
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)
    
    # Esegui migrazioni dinamiche per le colonne Discogs se il database esisteva già
    cursor = conn.cursor()
    
    # Verifica colonne ALBUM
    cursor.execute("PRAGMA table_info(ALBUM)")
    album_cols = [row[1] for row in cursor.fetchall()]
    if "discogs_id" not in album_cols:
        try:
            cursor.execute("ALTER TABLE ALBUM ADD COLUMN discogs_id INTEGER UNIQUE;")
            print("[MIGRATION] Aggiunta colonna discogs_id a ALBUM")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione discogs_id su ALBUM: {e}")
            
    if "tracklist" not in album_cols:
        try:
            cursor.execute("ALTER TABLE ALBUM ADD COLUMN tracklist TEXT;")
            print("[MIGRATION] Aggiunta colonna tracklist a ALBUM")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione tracklist su ALBUM: {e}")

    if "label" not in album_cols:
        try:
            cursor.execute("ALTER TABLE ALBUM ADD COLUMN label VARCHAR(100);")
            print("[MIGRATION] Aggiunta colonna label a ALBUM")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione label su ALBUM: {e}")

    if "catno" not in album_cols:
        try:
            cursor.execute("ALTER TABLE ALBUM ADD COLUMN catno VARCHAR(50);")
            print("[MIGRATION] Aggiunta colonna catno a ALBUM")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione catno su ALBUM: {e}")

    if "barcode" not in album_cols:
        try:
            cursor.execute("ALTER TABLE ALBUM ADD COLUMN barcode VARCHAR(50);")
            print("[MIGRATION] Aggiunta colonna barcode a ALBUM")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione barcode su ALBUM: {e}")

    if "country" not in album_cols:
        try:
            cursor.execute("ALTER TABLE ALBUM ADD COLUMN country VARCHAR(50);")
            print("[MIGRATION] Aggiunta colonna country a ALBUM")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione country su ALBUM: {e}")
            
    # Verifica colonne ARTIST
    cursor.execute("PRAGMA table_info(ARTIST)")
    artist_cols = [row[1] for row in cursor.fetchall()]
    if "discogs_id" not in artist_cols:
        try:
            cursor.execute("ALTER TABLE ARTIST ADD COLUMN discogs_id INTEGER UNIQUE;")
            print("[MIGRATION] Aggiunta colonna discogs_id a ARTIST")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione discogs_id su ARTIST: {e}")
            
    if "biography" not in artist_cols:
        try:
            cursor.execute("ALTER TABLE ARTIST ADD COLUMN biography TEXT;")
            print("[MIGRATION] Aggiunta colonna biography a ARTIST")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione biography su ARTIST: {e}")
            
    if "image_path" not in artist_cols:
        try:
            cursor.execute("ALTER TABLE ARTIST ADD COLUMN image_path VARCHAR(255);")
            print("[MIGRATION] Aggiunta colonna image_path a ARTIST")
        except Exception as e:
            print(f"[MIGRATION WARNING] Errore migrazione image_path su ARTIST: {e}")

    # Verifica se la tabella ALBUM ha il CHECK constraint
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='ALBUM'")
    album_sql_row = cursor.fetchone()
    if album_sql_row and "CHECK" in album_sql_row[0]:
        print("[MIGRATION] Rilevato CHECK constraint su ALBUM. Rimozione in corso...")
        try:
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("ALTER TABLE ALBUM RENAME TO ALBUM_old;")
            cursor.execute("""
                CREATE TABLE ALBUM (
                    id_album        INTEGER     PRIMARY KEY AUTOINCREMENT,
                    title           VARCHAR(100)    NOT NULL,
                    releaseYear     INTEGER,
                    genre           VARCHAR(100),
                    coverPath       VARCHAR(255),
                    id_user         INTEGER         DEFAULT NULL,
                    discogs_id      INTEGER         UNIQUE,
                    tracklist       TEXT,
                    label           VARCHAR(100),
                    catno           VARCHAR(50),
                    barcode         VARCHAR(50),
                    country         VARCHAR(50),
                    FOREIGN KEY (id_user) REFERENCES USER(id_user) ON DELETE SET NULL
                );
            """)
            cursor.execute("""
                INSERT INTO ALBUM (id_album, title, releaseYear, genre, coverPath, id_user, discogs_id, tracklist, label, catno, barcode, country)
                SELECT id_album, title, releaseYear, genre, coverPath, id_user, discogs_id, tracklist, label, catno, barcode, country
                FROM ALBUM_old;
            """)
            cursor.execute("DROP TABLE ALBUM_old;")
            cursor.execute("PRAGMA foreign_keys = ON;")
            print("[MIGRATION] Rimozione CHECK constraint completata con successo.")
        except Exception as e:
            print(f"[MIGRATION ERROR] Impossibile rimuovere il CHECK constraint: {e}")

    conn.commit()
    conn.close()
    print(f"[OK] Schema database verificato/inizializzato: {Config.DATABASE_PATH}")


def seed_db():
    """Esegue il seeding dei dati iniziali nel database se non sono presenti record utente."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    count = conn.execute("SELECT COUNT(*) FROM USER").fetchone()[0]
    if count > 0:
        conn.close()
        print("[OK] Seed saltato: il database contiene gia' dei dati")
        return

    # Inserimento dell'amministratore di default (admin / admin)
    conn.execute(
        """INSERT INTO USER (username, name, surname, email, passwordHash, role)
           VALUES (?, ?, ?, ?, ?, ?)""",
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
    conn.execute(
        """INSERT INTO USER (username, name, surname, email, passwordHash, role)
           VALUES (?, ?, ?, ?, ?, ?)""",
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
    conn.close()
    print("[OK] Seed completato: creati utenti admin e test")


if __name__ == "__main__":
    init_db()
    seed_db()

    conn = get_db()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = [row["name"] for row in cursor.fetchall()]

    users = conn.execute(
        "SELECT id_user, username, role FROM USER"
    ).fetchall()
    conn.close()

    print(f"[OK] Tabelle presenti nel database: {tables}")
    print(f"[OK] Utenti nel database:")
    for u in users:
        print(f"     - {u['username']} (ruolo: {u['role']})")


