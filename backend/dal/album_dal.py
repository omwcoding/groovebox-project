"""
GrooveBox - Data Access Layer per Album
=======================================
Gestisce la persistenza e le query SQL per la tabella ALBUM e le relazioni
ponte associate (ALBUM_ARTIST).
"""

from core.database import get_db
import json

def get_album_artists(album_id):
    """Recupera l'elenco degli artisti associati a un determinato album."""
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
    """Arricchisce un record di tipo ALBUM con la lista dei relativi artisti associati."""
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
    albums = conn.execute(
        "SELECT al.*, us.username AS creator_username "
        "FROM ALBUM al "
        "LEFT JOIN USER us ON al.id_user = us.id_user "
        "ORDER BY al.id_album DESC"
    ).fetchall()
    return [enrich_album(a) for a in albums]

def find_album_by_id(album_id):
    """Cerca un singolo album a partire dal suo identificativo univoco."""
    conn = get_db()
    album = conn.execute(
        "SELECT al.*, us.username AS creator_username "
        "FROM ALBUM al "
        "LEFT JOIN USER us ON al.id_user = us.id_user "
        "WHERE al.id_album = ?", (album_id,)
    ).fetchone()
    return enrich_album(album)


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
        cursor = conn.execute(
            """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user, discogs_id, tracklist, label, catno, barcode, country)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title.strip(), release_year, genre, cover_path, creator_user_id, discogs_id, tracklist_str, label, catno, barcode, country)
        )
        album_id = cursor.lastrowid
        
        for aid in artist_ids:
            conn.execute(
                "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
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
    """
    Elimina un album dal catalogo per identificativo. 
    L'eliminazione propaga a cascata sulle copie fisiche e sulla tabella ponte.
    """
    conn = get_db()
    with conn:
        # Nota: Grazie a ON DELETE CASCADE, eliminiamo solo l'album
        # e SQLite rimuove automaticamente ALBUM_ARTIST e PHYSICAL_COPY associate.
        conn.execute("DELETE FROM ALBUM WHERE id_album = ?", (album_id,))

def update_album_cover(album_id, filename):
    """Aggiorna il percorso del file immagine associato alla copertina dell'album."""
    conn = get_db()
    with conn:
        conn.execute("UPDATE ALBUM SET coverPath = ? WHERE id_album = ?", (filename, album_id))


def search_albums_local(query, limit=10):
    """Cerca gli album nel database locale in base al titolo o al nome dell'artista."""
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT al.* 
           FROM ALBUM al
           LEFT JOIN ALBUM_ARTIST aa ON al.id_album = aa.id_album
           LEFT JOIN ARTIST ar ON aa.id_artist = ar.id_artist
           WHERE al.title LIKE ? OR ar.name LIKE ?
           LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    return [enrich_album(r) for r in rows]
