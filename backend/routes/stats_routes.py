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
from dal.stats_dal import get_platform_stats

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

    try:
        stats = get_platform_stats()
        return jsonify({
            "status": "success",
            "data": stats
        })
    except Exception:
        return jsonify({"status": "error", "message": "Errore nel caricamento delle statistiche"}), 500
