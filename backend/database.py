"""
GrooveBox – Data Access Layer (Step 1)
======================================
Genera fisicamente il file `groovebox.db` con le 5 tabelle definite nel
modello relazionale del documento di progetto (Capitolo 3.2).

Tabelle:
    USER, ALBUM, ARTIST, ALBUM_ARTIST, PHYSICAL_COPY

Uso standalone (crea / ricrea il database):
    python database.py
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from flask import g, has_app_context

from config import Config

# ---------------------------------------------------------------------------
# Helper: connessione al database
# ---------------------------------------------------------------------------

def get_db():
    """Restituisce una connessione SQLite con foreign keys abilitate e
    row_factory impostata su sqlite3.Row. Se all'interno del contesto Flask,
    la connessione viene salvata in g per essere chiusa automaticamente al teardown."""
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

# ---------------------------------------------------------------------------
# Schema DDL – esattamente aderente al modello relazionale (doc §3.2)
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- =========================================================================
-- TABELLA: USER
-- Identifica tutti i soggetti registrati sulla piattaforma.
-- L'attributo 'role' discrimina tra 'collector' e 'administrator'.
-- =========================================================================
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

-- =========================================================================
-- TABELLA: ALBUM
-- Anagrafica globale e condivisa dei dischi (catalogo comunitario).
-- FK id_user → USER  (relazione INSERTS 1:N – chi ha inserito l'album).
-- =========================================================================
CREATE TABLE IF NOT EXISTS ALBUM (
    id_album        INTEGER     PRIMARY KEY AUTOINCREMENT,
    title           VARCHAR(100)    NOT NULL,
    releaseYear     INTEGER,
    genre           VARCHAR(50),
    coverPath       VARCHAR(255),
    id_user         INTEGER         NOT NULL,

    FOREIGN KEY (id_user) REFERENCES USER(id_user)
);

-- =========================================================================
-- TABELLA: ARTIST
-- Singoli artisti o gruppi musicali autori degli album.
-- =========================================================================
CREATE TABLE IF NOT EXISTS ARTIST (
    id_artist       INTEGER     PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)    NOT NULL
);

-- =========================================================================
-- TABELLA: ALBUM_ARTIST  (tabella ponte – relazione PUBLISHES N:M)
-- Associa artisti e album. Chiave primaria composta (id_album, id_artist).
-- =========================================================================
CREATE TABLE IF NOT EXISTS ALBUM_ARTIST (
    id_album        INTEGER     NOT NULL,
    id_artist       INTEGER     NOT NULL,

    PRIMARY KEY (id_album, id_artist),
    FOREIGN KEY (id_album)  REFERENCES ALBUM(id_album) ON DELETE CASCADE,
    FOREIGN KEY (id_artist) REFERENCES ARTIST(id_artist) ON DELETE CASCADE
);

-- =========================================================================
-- TABELLA: PHYSICAL_COPY
-- Specifico supporto fisico (vinile, CD, cassetta) posseduto da un utente.
-- FK id_user  → USER  (relazione OWNS   1:N)
-- FK id_album → ALBUM (relazione REFERS N:1)
-- =========================================================================
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

# ---------------------------------------------------------------------------
# Inizializzazione del database
# ---------------------------------------------------------------------------

def init_db():
    """Crea (o ricrea) il file groovebox.db applicando lo schema DDL."""
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print(f"[OK] Database creato con successo: {Config.DATABASE_PATH}")


# ---------------------------------------------------------------------------
# Seed: popolamento iniziale con utenti di default
# ---------------------------------------------------------------------------

def seed_db():
    """Inserisce i dati iniziali se il database e' vuoto."""
    conn = get_db()

    # Controlla se esistono gia' utenti
    count = conn.execute("SELECT COUNT(*) FROM USER").fetchone()[0]
    if count > 0:
        conn.close()
        print("[OK] Seed saltato: il database contiene gia' dei dati")
        return

    # 1. Amministratore di default  (admin / admin)
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

    # 2. Collector di esempio  (mario_rossi / password123)
    conn.execute(
        """INSERT INTO USER (username, name, surname, email, passwordHash, role)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            "mario_rossi",
            "Mario",
            "Rossi",
            "mario.rossi@email.com",
            generate_password_hash("password123"),
            "collector"
        )
    )

    conn.commit()
    conn.close()
    print("[OK] Seed completato: creati utenti admin e mario_rossi")


# ---------------------------------------------------------------------------
# Entry-point diretto
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    seed_db()

    # Verifica rapida: elenca le tabelle create
    conn = get_db()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = [row["name"] for row in cursor.fetchall()]

    # Mostra gli utenti inseriti dal seed
    users = conn.execute(
        "SELECT id_user, username, role FROM USER"
    ).fetchall()
    conn.close()

    print(f"[OK] Tabelle presenti nel database: {tables}")
    print(f"[OK] Utenti nel database:")
    for u in users:
        print(f"     - {u['username']} (ruolo: {u['role']})")

