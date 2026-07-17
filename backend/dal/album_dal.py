"""
Mint - Data Access Layer per Album
=======================================
Gestisce la persistenza e le query SQL per la tabella albums e le relazioni
ponte associate (album_artists) nel database PostgreSQL.
"""

from core.database import get_db
import json

def get_album_artists(album_id):
    """Recupera l'elenco degli artisti associati a un determinato album."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT ar.id_artist, ar.name
               FROM artists ar
               JOIN album_artists aa ON ar.id_artist = aa.id_artist
               WHERE aa.id_album = %s
               ORDER BY ar.name;""",
            (album_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()

def enrich_album(album_row):
    """Arricchisce un record di tipo album con la lista dei relativi artisti associati."""
    if not album_row:
        return None
    album_dict = dict(album_row)
    artists = get_album_artists(album_dict["id_album"])
    album_dict["artists"] = [dict(a) for a in artists]
    
    # Decodifica tracklist da JSON string a lista Python
    if "tracklist" in album_dict and album_dict["tracklist"]:
        try:
            album_dict["tracklist"] = json.loads(album_dict["tracklist"])
        except Exception:
            album_dict["tracklist"] = []
    else:
        album_dict["tracklist"] = []
        
    return album_dict

def get_all_albums():
    """Recupera tutti gli album presenti nel catalogo globale, ordinati decrescentemente per ID."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT al.*, us.username AS creator_username "
            "FROM albums al "
            "LEFT JOIN users us ON al.id_user = us.id_user "
            "ORDER BY al.id_album DESC;"
        )
        albums = cursor.fetchall()
        return [enrich_album(a) for a in albums]
    finally:
        cursor.close()

def find_album_by_id(album_id):
    """Cerca un singolo album a partire dal suo identificativo univoco."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT al.*, us.username AS creator_username "
            "FROM albums al "
            "LEFT JOIN users us ON al.id_user = us.id_user "
            "WHERE al.id_album = %s;", (album_id,)
        )
        album = cursor.fetchone()
        return enrich_album(album)
    finally:
        cursor.close()

def insert_album(title, release_year, genre, artist_ids, creator_user_id, discogs_id=None, tracklist=None, cover_path=None, label=None, catno=None, barcode=None, country=None):
    """Inserisce un nuovo record album e crea le relative associazioni con gli artisti."""
    conn = get_db()
    
    tracklist_str = None
    if tracklist is not None:
        if isinstance(tracklist, (list, dict)):
            tracklist_str = json.dumps(tracklist)
        else:
            tracklist_str = tracklist

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO albums (title, release_year, genre, cover_path, id_user, discogs_id, tracklist, label, catno, barcode, country)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_album;""",
                (title.strip(), release_year, genre, cover_path, creator_user_id, discogs_id, tracklist_str, label, catno, barcode, country)
            )
            row = cursor.fetchone()
            album_id = row["id_album"] if row else None
            
            for aid in artist_ids:
                cursor.execute(
                    "INSERT INTO album_artists (id_album, id_artist) VALUES (%s, %s);",
                    (album_id, aid)
                )
            return album_id

def update_album_data(album_id, fields, values, artist_ids=None):
    """
    Aggiorna i metadati di un album e ne sincronizza le associazioni con gli artisti.
    
    Per prevenire vulnerabilità SQL Injection, l'argomento 'fields' deve contenere 
    esclusivamente identificatori di colonna statici definiti dall'applicazione, 
    mentre i dati dinamici devono essere passati tramite l'argomento 'values'.
    """
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            if fields:
                query = f"UPDATE albums SET {', '.join(fields)} WHERE id_album = %s;"
                cursor.execute(query, values + [album_id])
            
            if artist_ids is not None:
                cursor.execute("DELETE FROM album_artists WHERE id_album = %s;", (album_id,))
                for aid in artist_ids:
                    cursor.execute(
                        "INSERT INTO album_artists (id_album, id_artist) VALUES (%s, %s);",
                        (album_id, aid)
                    )
    return find_album_by_id(album_id)

def delete_album_by_id(album_id):
    """
    Elimina un album dal catalogo per identificativo. 
    L'eliminazione propaga a cascata sulle copie fisiche e sulla tabella ponte.
    """
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM albums WHERE id_album = %s;", (album_id,))

def update_album_cover(album_id, filename):
    """Aggiorna il percorso del file immagine associato alla copertina dell'album."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE albums SET cover_path = %s WHERE id_album = %s;", (filename, album_id))

def search_albums_local(query, limit=10):
    """Cerca gli album nel database locale in base al titolo o al nome dell'artista."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT DISTINCT al.* 
               FROM albums al
               LEFT JOIN album_artists aa ON al.id_album = aa.id_album
               LEFT JOIN artists ar ON aa.id_artist = ar.id_artist
               WHERE al.title ILIKE %s OR ar.name ILIKE %s
               LIMIT %s;""",
            (f"%{query}%", f"%{query}%", limit)
        )
        rows = cursor.fetchall()
        return [enrich_album(r) for r in rows]
    finally:
        cursor.close()

def count_albums_by_cover_path(cover_path):
    """Conta quanti album utilizzano un determinato percorso di copertina."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM albums WHERE cover_path = %s;", (cover_path,))
        row = cursor.fetchone()
        return row["total"] if row else 0
    finally:
        cursor.close()

