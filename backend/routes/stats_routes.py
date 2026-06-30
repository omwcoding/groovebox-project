"""
GrooveBox - Rotte Statistiche
==============================
Blueprint: /api/stats

Matrice di visibilita' (doc 2.1 - Goal):
  Administrator -> Monitoraggio e Statistiche: R
                   Visualizzare le statistiche di utilizzo della piattaforma.
"""

from flask import Blueprint, jsonify, g
from auth import token_required
from database import get_db

bp = Blueprint("stats", __name__, url_prefix="/api/stats")


# --------------------------------------------------------------------------
# GET /api/stats
# Dashboard statistiche della piattaforma (solo Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_stats():
    if g.current_user["role"] != "administrator":
        return jsonify({
            "status": "error",
            "message": "Accesso riservato agli amministratori"
        }), 403

    conn = get_db()

    # Contatori generali
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

    # Formati piu' diffusi (distribuzione copie fisiche per formato)
    formats = conn.execute(
        """SELECT format, COUNT(*) as count
           FROM PHYSICAL_COPY
           GROUP BY format
           ORDER BY count DESC"""
    ).fetchall()

    # Album piu' collezionati (con piu' copie fisiche associate)
    top_albums = conn.execute(
        """SELECT al.id_album, al.title, COUNT(pc.id_copy) as copies_count
           FROM ALBUM al
           JOIN PHYSICAL_COPY pc ON al.id_album = pc.id_album
           GROUP BY al.id_album
           ORDER BY copies_count DESC
           LIMIT 10"""
    ).fetchall()

    # Ultimi album aggiunti al catalogo
    recent_albums = conn.execute(
        """SELECT id_album, title, genre, releaseYear
           FROM ALBUM
           ORDER BY id_album DESC
           LIMIT 5"""
    ).fetchall()

    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "totals": {
                "users": total_users,
                "albums": total_albums,
                "artists": total_artists,
                "physical_copies": total_copies
            },
            "formats_distribution": [dict(f) for f in formats],
            "top_collected_albums": [dict(a) for a in top_albums],
            "recent_albums": [dict(a) for a in recent_albums]
        }
    })
