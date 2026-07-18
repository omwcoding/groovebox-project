-- Mint - DDL Schema per Supabase (PostgreSQL)
-- ==============================================================================
-- Questo script definisce la struttura delle tabelle ed abilita la Row Level Security.
-- Viene eseguito automaticamente dallo script backend/scripts/reset_db.py.

-- 1. Rimozione tabelle esistenti (se presenti) per reset completo
DROP TABLE IF EXISTS wishlists CASCADE;
DROP TABLE IF EXISTS admin_audit_logs CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS discogs_cache CASCADE;
DROP TABLE IF EXISTS physical_copies CASCADE;
DROP TABLE IF EXISTS album_artists CASCADE;
DROP TABLE IF EXISTS artists CASCADE;
DROP TABLE IF EXISTS albums CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 2. Creazione Tabella: users
CREATE TABLE users (
    id_user         SERIAL          PRIMARY KEY,
    username        VARCHAR(30)     NOT NULL UNIQUE,
    name            VARCHAR(50)     NOT NULL,
    surname         VARCHAR(50)     NOT NULL,
    email           VARCHAR(100)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'collector'
                                    CHECK (role IN ('collector', 'administrator')),
    is_public       BOOLEAN         NOT NULL DEFAULT FALSE,
    bio             TEXT,
    avatar_path     VARCHAR(255),
    is_banned       BOOLEAN         NOT NULL DEFAULT FALSE
);

-- 3. Creazione Tabella: albums
CREATE TABLE albums (
    id_album        SERIAL          PRIMARY KEY,
    title           VARCHAR(100)    NOT NULL,
    release_year    INTEGER,
    genre           VARCHAR(100),
    cover_path      VARCHAR(255),
    id_user         INTEGER         DEFAULT NULL,
    discogs_id      INTEGER         UNIQUE,
    tracklist       TEXT,
    label           VARCHAR(100),
    catno           VARCHAR(50),
    barcode         VARCHAR(50),
    country         VARCHAR(50),

    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE SET NULL
);

-- 4. Creazione Tabella: artists
CREATE TABLE artists (
    id_artist       SERIAL          PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    discogs_id      INTEGER         UNIQUE,
    biography       TEXT,
    image_path      VARCHAR(255)
);

-- 5. Creazione Tabella: album_artists (Relazione Molti-a-Molti)
CREATE TABLE album_artists (
    id_album        INTEGER     NOT NULL,
    id_artist       INTEGER     NOT NULL,

    PRIMARY KEY (id_album, id_artist),
    FOREIGN KEY (id_album)  REFERENCES albums(id_album) ON DELETE CASCADE,
    FOREIGN KEY (id_artist) REFERENCES artists(id_artist) ON DELETE CASCADE
);

-- 6. Creazione Tabella: physical_copies
CREATE TABLE physical_copies (
    id_copy         SERIAL          PRIMARY KEY,
    format          VARCHAR(20)     NOT NULL CHECK (format IN ('Vinile', 'CD', 'Cassetta')),
    condition       VARCHAR(50)     NOT NULL CHECK (condition IN ('Nuovo', 'Come nuovo', 'Buono', 'Discreto', 'Rovinato')),
    added_date       DATE            NOT NULL,
    personal_notes   TEXT,
    id_user         INTEGER         NOT NULL,
    id_album        INTEGER         NOT NULL,

    FOREIGN KEY (id_user)  REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_album) REFERENCES albums(id_album) ON DELETE CASCADE
);

-- 7. Creazione Tabella: discogs_cache
CREATE TABLE discogs_cache (
    cache_key       VARCHAR(255)    PRIMARY KEY,
    response_json   TEXT            NOT NULL,
    cached_at       VARCHAR(100)    NOT NULL
);

-- 8. Creazione Tabella: wishlists
CREATE TABLE wishlists (
    id_wishlist     SERIAL          PRIMARY KEY,
    id_user         INTEGER         NOT NULL,
    id_album        INTEGER         DEFAULT NULL,
    discogs_id      INTEGER,
    title           VARCHAR(100),
    artist_name     VARCHAR(100),
    cover_url       VARCHAR(255),
    added_date       DATE            NOT NULL,
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_album) REFERENCES albums(id_album) ON DELETE SET NULL
);

-- 9. Creazione Tabella: reports
CREATE TABLE reports (
    id_report       SERIAL PRIMARY KEY,
    id_reporter     INTEGER NOT NULL REFERENCES users(id_user) ON DELETE CASCADE,
    id_reported     INTEGER NOT NULL REFERENCES users(id_user) ON DELETE CASCADE,
    category        VARCHAR(50) NOT NULL,
    details         TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMP,
    CHECK (id_reporter <> id_reported)
);

-- 10. Creazione Tabella: admin_audit_logs
CREATE TABLE admin_audit_logs (
    id_log          SERIAL PRIMARY KEY,
    id_admin        INTEGER NOT NULL REFERENCES users(id_user) ON DELETE RESTRICT,
    action_type     VARCHAR(50) NOT NULL,
    target_id       INTEGER,
    details         TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 11. Abilitazione Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE artists ENABLE ROW LEVEL SECURITY;
ALTER TABLE album_artists ENABLE ROW LEVEL SECURITY;
ALTER TABLE physical_copies ENABLE ROW LEVEL SECURITY;
ALTER TABLE wishlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE discogs_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;
