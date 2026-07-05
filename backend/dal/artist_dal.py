from core.database import get_db

def get_all_artists():
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST ORDER BY name").fetchall()

def find_artist_by_id(artist_id):
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST WHERE id_artist = ?", (artist_id,)).fetchone()

def find_artist_by_name(name):
    conn = get_db()
    return conn.execute("SELECT * FROM ARTIST WHERE LOWER(name) = LOWER(?)", (name.strip(),)).fetchone()

def get_artist_albums(artist_id):
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
    conn = get_db()
    with conn:
        cursor = conn.execute("INSERT INTO ARTIST (name) VALUES (?)", (name.strip(),))
        return cursor.lastrowid

def update_artist_name(artist_id, name):
    conn = get_db()
    with conn:
        conn.execute("UPDATE ARTIST SET name = ? WHERE id_artist = ?", (name.strip(), artist_id))
    return {"id_artist": artist_id, "name": name.strip()}

def delete_artist_by_id(artist_id):
    conn = get_db()
    with conn:
        # Nota: ALBUM_ARTIST verrà ripulito in automatico via ON DELETE CASCADE del DB
        conn.execute("DELETE FROM ARTIST WHERE id_artist = ?", (artist_id,))
