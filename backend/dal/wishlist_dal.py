from core.database import get_db
import datetime

def get_user_wishlist(user_id):
    """Recupera la wishlist di un utente, arricchita con dettagli dell'album se presenti localmente."""
    conn = get_db()
    rows = conn.execute(
        """SELECT w.*, al.coverPath AS local_cover_path, al.title AS local_title, al.genre AS local_genre
           FROM WISHLIST w
           LEFT JOIN ALBUM al ON w.id_album = al.id_album
           WHERE w.id_user = ?
           ORDER BY w.addedDate DESC""",
        (user_id,)
    ).fetchall()
    
    results = []
    for r in rows:
        item = dict(r)
        if item["id_album"]:
            from dal.album_dal import get_album_artists
            artists = get_album_artists(item["id_album"])
            item["artists"] = [dict(a) for a in artists]
        else:
            item["artists"] = []
        results.append(item)
    return results

def add_to_wishlist(user_id, id_album=None, discogs_id=None, title=None, artist_name=None, cover_url=None):
    """Aggiunge un elemento alla wishlist dell'utente."""
    conn = get_db()
    added_date = datetime.date.today().isoformat()
    with conn:
        cursor = conn.execute(
            """INSERT INTO WISHLIST (id_user, id_album, discogs_id, title, artist_name, cover_url, addedDate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, id_album, discogs_id, title, artist_name, cover_url, added_date)
        )
        return cursor.lastrowid

def delete_from_wishlist(wishlist_id):
    """Rimuove un elemento dalla wishlist tramite id."""
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM WISHLIST WHERE id_wishlist = ?", (wishlist_id,))

def find_wishlist_by_id_and_user(wishlist_id, user_id):
    """Trova un elemento in wishlist per ID e ID utente."""
    conn = get_db()
    return conn.execute(
        "SELECT * FROM WISHLIST WHERE id_wishlist = ? AND id_user = ?",
        (wishlist_id, user_id)
    ).fetchone()
