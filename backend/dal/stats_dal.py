"""
GrooveBox - Data Access Layer per le Statistiche
================================================
Raggruppa le query SQL aggregate e analitiche utilizzate per popolare i widget 
e la dashboard di monitoraggio amministrativo della piattaforma nel database PostgreSQL.
"""

from core.database import get_db

def get_platform_stats():
    """
    Esegue query analitiche aggregate sul database e restituisce le metriche di 
    utilizzo, tra cui totali, distribuzione dei supporti, generi e classifiche utenti.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Metriche complessive
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'collector';")
        row = cursor.fetchone()
        total_users = row["total"] if row else 0

        cursor.execute("SELECT COUNT(*) AS total FROM albums;")
        row = cursor.fetchone()
        total_albums = row["total"] if row else 0

        cursor.execute("SELECT COUNT(*) AS total FROM artists;")
        row = cursor.fetchone()
        total_artists = row["total"] if row else 0

        cursor.execute("SELECT COUNT(*) AS total FROM physical_copies;")
        row = cursor.fetchone()
        total_copies = row["total"] if row else 0

        # Distribuzione percentuale dei supporti fisici per formato
        cursor.execute(
            """SELECT format, COUNT(*) as count
               FROM physical_copies
               GROUP BY format
               ORDER BY count DESC;"""
        )
        formats = cursor.fetchall()

        # Top 10 degli album più collezionati
        cursor.execute(
            """SELECT al.id_album, al.title, COUNT(pc.id_copy) as copies_count
               FROM albums al
               JOIN physical_copies pc ON al.id_album = pc.id_album
               GROUP BY al.id_album, al.title
               ORDER BY copies_count DESC
               LIMIT 10;"""
        )
        top_albums = cursor.fetchall()

        # Elenco degli ultimi album inseriti a catalogo
        cursor.execute(
            """SELECT id_album, title, genre, release_year, cover_path
               FROM albums
               ORDER BY id_album DESC
               LIMIT 5;"""
        )
        recent_albums = cursor.fetchall()

        # Distribuzione degli album per genere musicale
        cursor.execute(
            """SELECT genre, COUNT(*) as count
               FROM albums
               WHERE genre IS NOT NULL AND genre != ''
               GROUP BY genre
               ORDER BY count DESC
               LIMIT 5;"""
        )
        genres = cursor.fetchall()

        # Classifica degli utenti con il maggior numero di copie fisiche registrate
        cursor.execute(
            """SELECT u.username, u.name, u.surname, COUNT(pc.id_copy) as copies_count
               FROM users u
               JOIN physical_copies pc ON u.id_user = pc.id_user
               GROUP BY u.id_user, u.username, u.name, u.surname
               ORDER BY copies_count DESC
               LIMIT 5;"""
        )
        collectors = cursor.fetchall()

        # Classifica degli artisti con il maggior numero di album registrati
        cursor.execute(
            """SELECT ar.id_artist, ar.name, COUNT(DISTINCT aa.id_album) as albums_count
               FROM artists ar
               JOIN album_artists aa ON ar.id_artist = aa.id_artist
               GROUP BY ar.id_artist, ar.name
               ORDER BY albums_count DESC
               LIMIT 5;"""
        )
        top_artists = cursor.fetchall()

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
    finally:
        cursor.close()
