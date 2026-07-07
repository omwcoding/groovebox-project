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

def insert_artist(name):
    """Inserisce un nuovo artista a catalogo."""
    conn = get_db()
    with conn:
        cursor = conn.execute("INSERT INTO ARTIST (name) VALUES (?)", (name.strip(),))
        return cursor.lastrowid

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

