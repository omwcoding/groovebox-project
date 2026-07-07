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
    genre           VARCHAR(50)     CHECK (genre IS NULL OR genre IN ('Rock / Alternative', 'Pop', 'Hip-Hop / Rap', 'Electronic / Dance', 'Ambient / Experimental', 'Metal / Hard Rock', 'Jazz / Blues', 'Soul / R&B / Funk', 'Reggae / Dub', 'Folk / Acoustic', 'Classical', 'Soundtrack / OST', 'World / Altro')),
    coverPath       VARCHAR(255),
    id_user         INTEGER         DEFAULT NULL,

    FOREIGN KEY (id_user) REFERENCES USER(id_user) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ARTIST (
    id_artist       INTEGER     PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)    NOT NULL
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
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)
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


