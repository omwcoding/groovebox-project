import datetime
from core.database import get_db
from dal.album_dal import get_album_artists

def enrich_copy(copy_row):
    if not copy_row:
        return None
    copy_dict = dict(copy_row)
    artists = get_album_artists(copy_dict["id_album"])
    copy_dict["artists"] = [dict(a) for a in artists]
    return copy_dict

def get_user_copies(user_id):
    conn = get_db()
    copies = conn.execute(
        """SELECT pc.*, al.title AS album_title, al.releaseYear, al.genre, al.coverPath
           FROM PHYSICAL_COPY pc
           JOIN ALBUM al ON pc.id_album = al.id_album
           WHERE pc.id_user = ?
           ORDER BY pc.addedDate DESC""",
        (user_id,)
    ).fetchall()
    return [enrich_copy(c) for c in copies]

def find_copy_by_id_and_user(copy_id, user_id):
    conn = get_db()
    copy = conn.execute(
        """SELECT pc.*, al.title AS album_title, al.releaseYear, al.genre, al.coverPath
           FROM PHYSICAL_COPY pc
           JOIN ALBUM al ON pc.id_album = al.id_album
           WHERE pc.id_copy = ? AND pc.id_user = ?""",
        (copy_id, user_id)
    ).fetchone()
    return enrich_copy(copy)

def insert_copy(id_album, format_val, condition, personal_notes, user_id):
    conn = get_db()
    added_date = datetime.date.today().isoformat()
    with conn:
        cursor = conn.execute(
            """INSERT INTO PHYSICAL_COPY
               (format, condition, addedDate, personalNotes, id_user, id_album)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (format_val.strip(), condition.strip(), added_date, personal_notes, user_id, id_album)
        )
        copy_id = cursor.lastrowid
    return copy_id

def create_copy_cascade(title, artist_ids, release_year, genre, format_val, condition, personal_notes, user_id):
    conn = get_db()
    added_date = datetime.date.today().isoformat()
    with conn:
        # 1. Trova o crea Album (usiamo il primo artista come pivot per la ricerca per evitare duplicati semplici)
        first_artist_id = artist_ids[0] if artist_ids else None
        
        album = None
        if first_artist_id:
            album = conn.execute(
                """SELECT al.id_album 
                   FROM ALBUM al 
                   JOIN ALBUM_ARTIST aa ON al.id_album = aa.id_album 
                   WHERE LOWER(al.title) = LOWER(?) AND aa.id_artist = ?""", 
                (title.strip(), first_artist_id)
            ).fetchone()

        if album:
            album_id = album["id_album"]
        else:
            cursor = conn.execute(
                """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user) 
                   VALUES (?, ?, ?, NULL, ?)""", 
                (title.strip(), release_year, genre, user_id)
            )
            album_id = cursor.lastrowid
            
            # Collega tutti gli artisti all'album
            for artist_id in artist_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)", 
                    (album_id, artist_id)
                )

        # 2. Registra la Copia Fisica
        cursor = conn.execute(
            """INSERT INTO PHYSICAL_COPY (format, condition, addedDate, personalNotes, id_user, id_album) 
               VALUES (?, ?, ?, ?, ?, ?)""", 
            (format_val.strip(), condition.strip(), added_date, personal_notes, user_id, album_id)
        )
        copy_id = cursor.lastrowid
        
        return copy_id

def update_copy_data(copy_id, fields, values):
    """
    Aggiorna i dati di una copia fisica.

    SICUREZZA: `fields` deve contenere SOLO stringhe colonna hardcoded
    (es. 'format = ?', 'condition = ?'), MAI valori provenienti dall'input utente.
    I valori utente vanno sempre e solo in `values`, passati come parametri
    alla query per sfruttare il prepared statement di sqlite3.
    """
    conn = get_db()
    with conn:
        query = f"UPDATE PHYSICAL_COPY SET {', '.join(fields)} WHERE id_copy = ?"
        conn.execute(query, values + [copy_id])

def delete_copy_by_id(copy_id):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM PHYSICAL_COPY WHERE id_copy = ?", (copy_id,))

def delete_all_copies_by_user(user_id):
    """Svuota l'intera collezione dell'utente eliminando tutte le sue copie fisiche."""
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM PHYSICAL_COPY WHERE id_user = ?", (user_id,))
