"""
GrooveBox - Data Access Layer per Artisti
=========================================
Gestisce le operazioni di persistenza, lettura e cancellazione per la 
tabella ARTIST e la consultazione della discografia ad essa associata.
"""

from core.database import get_db

def get_all_artists():
    """Recupera l'elenco completo degli artisti memorizzati, ordinati per nome."""
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST ORDER BY name").fetchall()

def find_artist_by_id(artist_id):
    """Cerca un singolo artista per identificativo univoco."""
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST WHERE id_artist = ?", (artist_id,)).fetchone()

def find_artist_by_discogs_id(discogs_id):
    """Cerca un singolo artista per ID Discogs."""
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST WHERE discogs_id = ?", (discogs_id,)).fetchone()

def find_artist_by_name(name):
    """Cerca un singolo artista per nome (senza distinzione tra maiuscole/minuscole)."""
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST WHERE LOWER(name) = ?", (name.strip().lower(),)).fetchone()

def get_artist_albums(artist_id):
    """Recupera tutti gli album associati a un determinato artista, ordinati per anno di uscita."""
    conn = get_db()
    return conn.execute(
        """SELECT al.id_album, al.title, al.releaseYear, al.genre
           FROM ALBUM al
           JOIN ALBUM_ARTIST aa ON al.id_album = aa.id_album
           WHERE aa.id_artist = ?
           ORDER BY al.releaseYear""",
        (artist_id,)
    ).fetchall()

def insert_artist(name, discogs_id=None, biography=None, image_path=None):
    """Inserisce un nuovo artista a catalogo."""
    conn = get_db()
    with conn:
        cursor = conn.execute(
            "INSERT INTO ARTIST (name, discogs_id, biography, image_path) VALUES (?, ?, ?, ?)",
            (name.strip(), discogs_id, biography, image_path)
        )
        return cursor.lastrowid

def update_artist_discogs_info(artist_id, discogs_id, biography, image_path):
    """Aggiorna le informazioni Discogs di un artista esistente."""
    conn = get_db()
    with conn:
        conn.execute(
            "UPDATE ARTIST SET discogs_id = ?, biography = ?, image_path = ? WHERE id_artist = ?",
            (discogs_id, biography, image_path, artist_id)
        )

def update_artist_name(artist_id, name):
    """Aggiorna la denominazione di un artista esistente."""
    conn = get_db()
    with conn:
        conn.execute("UPDATE ARTIST SET name = ? WHERE id_artist = ?", (name.strip(), artist_id))
    return {"id_artist": artist_id, "name": name.strip()}

def delete_artist_by_id(artist_id):
    """Elimina un artista dal catalogo. Le relazioni ponte vengono rimosse a cascata."""
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM ARTIST WHERE id_artist = ?", (artist_id,))

