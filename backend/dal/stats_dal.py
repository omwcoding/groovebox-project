"""
GrooveBox - Data Access Layer per le Statistiche
================================================
Raggruppa le query SQL aggregate e analitiche utilizzate per popolare i widget 
e la dashboard di monitoraggio amministrativo della piattaforma.
"""

from core.database import get_db

def get_platform_stats():
    """
    Esegue query analitiche aggregate sul database e restituisce le metriche di 
    utilizzo, tra cui totali, distribuzione dei supporti, generi e classifiche utenti.
    """
    conn = get_db()
    
    # Metriche complessive
    total_users = conn.execute(
        "SELECT COUNT(*) FROM USER WHERE role = 'collector'"
    ).fetchone()[0]

    total_albums = conn.execute(
        "SELECT COUNT(*) FROM ALBUM"
    ).fetchone()[0]

    total_artists = conn.execute(
        "SELECT COUNT(*) FROM ARTIST"
    ).fetchone()[0]

    total_copies = conn.execute(
        "SELECT COUNT(*) FROM PHYSICAL_COPY"
    ).fetchone()[0]

    # Distribuzione percentuale dei supporti fisici per formato
    formats = conn.execute(
        """SELECT format, COUNT(*) as count
           FROM PHYSICAL_COPY
           GROUP BY format
           ORDER BY count DESC"""
    ).fetchall()

    # Top 10 degli album più collezionati
    top_albums = conn.execute(
        """SELECT al.id_album, al.title, COUNT(pc.id_copy) as copies_count
           FROM ALBUM al
           JOIN PHYSICAL_COPY pc ON al.id_album = pc.id_album
           GROUP BY al.id_album
           ORDER BY copies_count DESC
           LIMIT 10"""
    ).fetchall()

    # Elenco degli ultimi album inseriti a catalogo
    recent_albums = conn.execute(
        """SELECT id_album, title, genre, releaseYear, coverPath
           FROM ALBUM
           ORDER BY id_album DESC
           LIMIT 5"""
    ).fetchall()

    # Distribuzione degli album per genere musicale
    genres = conn.execute(
        """SELECT genre, COUNT(*) as count
           FROM ALBUM
           WHERE genre IS NOT NULL AND genre != ''
           GROUP BY genre
           ORDER BY count DESC
           LIMIT 5"""
    ).fetchall()

    # Classifica degli utenti con il maggior numero di copie fisiche registrate
    collectors = conn.execute(
        """SELECT u.username, u.name, u.surname, COUNT(pc.id_copy) as copies_count
           FROM USER u
           JOIN PHYSICAL_COPY pc ON u.id_user = pc.id_user
           GROUP BY u.id_user
           ORDER BY copies_count DESC
           LIMIT 5"""
    ).fetchall()

    # Classifica degli artisti con il maggior numero di album registrati
    top_artists = conn.execute(
        """SELECT ar.id_artist, ar.name, COUNT(DISTINCT aa.id_album) as albums_count
           FROM ARTIST ar
           JOIN ALBUM_ARTIST aa ON ar.id_artist = aa.id_artist
           GROUP BY ar.id_artist
           ORDER BY albums_count DESC
           LIMIT 5"""
    ).fetchall()

    return {
        "totals": {
            "users": total_users,
            "albums": total_albums,
            "artists": total_artists,
            "physical_copies": total_copies
        },
        "formats_distribution": [dict(f) for f in formats],
        "top_collected_albums": [dict(a) for a in top_albums],
        "recent_albums": [dict(a) for a in recent_albums],
        "genres_distribution": [dict(g) for g in genres],
        "top_collectors": [dict(c) for c in collectors],
        "top_artists": [dict(a) for a in top_artists]
    }

