from core.database import get_db
import datetime
from dal.album_dal import get_album_artists

def get_user_wishlist(user_id):
    """Recupera la wishlist di un utente, arricchita con dettagli dell'album se presenti localmente."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT w.*, al.cover_path AS local_cover_path, al.title AS local_title, al.genre AS local_genre
               FROM wishlists w
               LEFT JOIN albums al ON w.id_album = al.id_album
               WHERE w.id_user = %s
               ORDER BY w.added_date DESC;""",
            (user_id,)
        )
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            item = dict(r)
            if item["id_album"]:
                artists = get_album_artists(item["id_album"])
                item["artists"] = [dict(a) for a in artists]
            else:
                item["artists"] = []
            results.append(item)
        return results
    finally:
        cursor.close()

def add_to_wishlist(user_id, id_album=None, discogs_id=None, title=None, artist_name=None, cover_url=None):
    """Aggiunge un elemento alla wishlist dell'utente."""
    conn = get_db()
    added_date = datetime.date.today().isoformat()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO wishlists (id_user, id_album, discogs_id, title, artist_name, cover_url, added_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_wishlist;""",
                (user_id, id_album, discogs_id, title, artist_name, cover_url, added_date)
            )
            row = cursor.fetchone()
            return row["id_wishlist"] if row else None

def delete_from_wishlist(wishlist_id):
    """Rimuove un elemento dalla wishlist tramite id."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM wishlists WHERE id_wishlist = %s;", (wishlist_id,))

def find_wishlist_by_id_and_user(wishlist_id, user_id):
    """Trova un elemento in wishlist per ID e ID utente."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM wishlists WHERE id_wishlist = %s AND id_user = %s;",
            (wishlist_id, user_id)
        )
        return cursor.fetchone()
    finally:
        cursor.close()

def promote_wishlist_item(wishlist_id, format_val, condition, personal_notes, user_id):
    """
    Promuove un elemento della wishlist a copia fisica nel Vault.
    Se l'album non è presente localmente, lo importa prima da Discogs.
    Rimuove l'elemento dalla wishlist al termine dell'operazione.
    Ritorna l'id della copia fisica creata.
    """
    item = find_wishlist_by_id_and_user(wishlist_id, user_id)
    if not item:
        raise ValueError("Elemento non trovato in wishlist")

    id_album = item["id_album"]
    if not id_album and item["discogs_id"]:
        from dal.discogs_import_dal import import_album_from_discogs
        id_album, _ = import_album_from_discogs(item["discogs_id"], user_id)

    if not id_album:
        raise ValueError("Impossibile promuovere elemento senza album locale valido")

    from dal.copy_dal import insert_copy
    copy_id = insert_copy(
        id_album=id_album,
        format_val=format_val,
        condition=condition,
        personal_notes=personal_notes,
        user_id=user_id
    )

    delete_from_wishlist(wishlist_id)
    return copy_id

