"""
GrooveBox - Rotte Statistiche
==============================
Blueprint: /api/stats

Matrice di visibilita' (doc 2.1 - Goal):
  Administrator -> Monitoraggio e Statistiche: R
                   Visualizzare le statistiche di utilizzo della piattaforma.
"""

from flask import Blueprint, jsonify, g
from core.auth import token_required
from dal.stats_dal import get_platform_stats
from core.errors import ForbiddenError

bp = Blueprint("stats", __name__, url_prefix="/api/stats")


# --------------------------------------------------------------------------
# GET /api/stats
# Dashboard statistiche della piattaforma (solo Admin).
# --------------------------------------------------------------------------
@bp.route("", methods=["GET"])
@token_required
def get_stats():
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    stats = get_platform_stats()
    return jsonify({
        "status": "success",
        "data": stats
    })


# --------------------------------------------------------------------------
# GET /api/stats/export
# Esporta il dump delle statistiche della piattaforma in JSON (solo Admin).
# --------------------------------------------------------------------------
@bp.route("/export", methods=["GET"])
@token_required
def export_stats():
    if g.current_user["role"] != "administrator":
        raise ForbiddenError("Accesso riservato agli amministratori")

    import json
    from flask import Response

    stats = get_platform_stats()
    json_data = json.dumps(stats, indent=4, ensure_ascii=False)

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=statistiche_groovebox.json"}
    )
