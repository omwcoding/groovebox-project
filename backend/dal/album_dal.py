from database import get_db

def get_album_artists(album_id):
    conn = get_db()
    return conn.execute(
        """SELECT ar.id_artist, ar.name
           FROM ARTIST ar
           JOIN ALBUM_ARTIST aa ON ar.id_artist = aa.id_artist
           WHERE aa.id_album = ?
           ORDER BY ar.name""",
        (album_id,)
    ).fetchall()

def enrich_album(album_row):
    if not album_row:
        return None
    album_dict = dict(album_row)
    artists = get_album_artists(album_dict["id_album"])
    album_dict["artists"] = [dict(a) for a in artists]
    return album_dict

def get_all_albums():
    conn = get_db()
    albums = conn.execute(
        "SELECT al.*, us.username AS creator_username "
        "FROM ALBUM al "
        "LEFT JOIN USER us ON al.id_user = us.id_user "
        "ORDER BY al.title"
    ).fetchall()
    return [enrich_album(a) for a in albums]

def find_album_by_id(album_id):
    conn = get_db()
    album = conn.execute(
        "SELECT al.*, us.username AS creator_username "
        "FROM ALBUM al "
        "LEFT JOIN USER us ON al.id_user = us.id_user "
        "WHERE al.id_album = ?", (album_id,)
    ).fetchone()
    return enrich_album(album)

def find_album_by_title_and_artist(title, artist_id):
    conn = get_db()
    album = conn.execute(
        """SELECT al.*, us.username AS creator_username
           FROM ALBUM al
           LEFT JOIN USER us ON al.id_user = us.id_user
           JOIN ALBUM_ARTIST aa ON al.id_album = aa.id_album
           WHERE LOWER(al.title) = LOWER(?) AND aa.id_artist = ?""",
        (title.strip(), artist_id)
    ).fetchone()
    return enrich_album(album)

def insert_album(title, release_year, genre, artist_ids, creator_user_id):
    conn = get_db()
    with conn:
        cursor = conn.execute(
            """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user)
               VALUES (?, ?, ?, NULL, ?)""",
            (title.strip(), release_year, genre, creator_user_id)
        )
        album_id = cursor.lastrowid
        
        for aid in artist_ids:
            conn.execute(
                "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                (album_id, aid)
            )
        return album_id

def update_album_data(album_id, fields, values, artist_ids=None):
    conn = get_db()
    with conn:
        if fields:
            query = f"UPDATE ALBUM SET {', '.join(fields)} WHERE id_album = ?"
            conn.execute(query, values + [album_id])
        
        if artist_ids is not None:
            conn.execute("DELETE FROM ALBUM_ARTIST WHERE id_album = ?", (album_id,))
            for aid in artist_ids:
                conn.execute(
                    "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                    (album_id, aid)
                )
    return find_album_by_id(album_id)

def delete_album_by_id(album_id):
    conn = get_db()
    with conn:
        # Nota: Grazie a ON DELETE CASCADE, eliminiamo solo l'album
        # e SQLite rimuove automaticamente ALBUM_ARTIST e PHYSICAL_COPY associate.
        conn.execute("DELETE FROM ALBUM WHERE id_album = ?", (album_id,))

def update_album_cover(album_id, filename):
    conn = get_db()
    with conn:
        conn.execute("UPDATE ALBUM SET coverPath = ? WHERE id_album = ?", (filename, album_id))
