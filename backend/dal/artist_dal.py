"""
GrooveBox - Data Access Layer per Artisti
=========================================
Gestisce le operazioni di persistenza, lettura e cancellazione per la 
tabella artists e la consultazione della discografia ad essa associata nel database PostgreSQL.
"""

from core.database import get_db

def get_all_artists():
    """Recupera l'elenco completo degli artisti memorizzati, ordinati per nome."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM artists ORDER BY name;")
        return cursor.fetchall()
    finally:
        cursor.close()

def find_artist_by_id(artist_id):
    """Cerca un singolo artista per identificativo univoco."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM artists WHERE id_artist = %s;", (artist_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

def find_artist_by_discogs_id(discogs_id):
    """Cerca un singolo artista per ID Discogs."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM artists WHERE discogs_id = %s;", (discogs_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

def find_artist_by_name(name):
    """Cerca un singolo artista per nome (senza distinzione tra maiuscole/minuscole)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM artists WHERE LOWER(name) = %s;", (name.strip().lower(),))
        return cursor.fetchone()
    finally:
        cursor.close()

def get_artist_albums(artist_id):
    """Recupera tutti gli album associati a un determinato artista, ordinati per anno di uscita."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT al.id_album, al.title, al.release_year, al.genre
               FROM albums al
               JOIN album_artists aa ON al.id_album = aa.id_album
               WHERE aa.id_artist = %s
               ORDER BY al.release_year;""",
            (artist_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()

def insert_artist(name, discogs_id=None, biography=None, image_path=None):
    """Inserisce un nuovo artista a catalogo."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO artists (name, discogs_id, biography, image_path) VALUES (%s, %s, %s, %s) RETURNING id_artist;",
                (name.strip(), discogs_id, biography, image_path)
            )
            row = cursor.fetchone()
            return row["id_artist"] if row else None

def update_artist_discogs_info(artist_id, discogs_id, biography, image_path):
    """Aggiorna le informazioni Discogs di un artista esistente."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE artists SET discogs_id = %s, biography = %s, image_path = %s WHERE id_artist = %s;",
                (discogs_id, biography, image_path, artist_id)
            )

def update_artist_name(artist_id, name):
    """Aggiorna la denominazione di un artista esistente."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE artists SET name = %s WHERE id_artist = %s;", (name.strip(), artist_id))
    return {"id_artist": artist_id, "name": name.strip()}

def delete_artist_by_id(artist_id):
    """Elimina un artista dal catalogo. Le relazioni ponte vengono rimosse a cascata."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM artists WHERE id_artist = %s;", (artist_id,))
