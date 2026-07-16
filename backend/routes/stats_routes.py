"""
Mint - Route Blueprint per Statistiche e Monitoraggio
=========================================================
Fornisce gli endpoint riservati agli amministratori per l'analisi 
aggregata dei dati e l'esportazione dei report in formato JSON.
"""

import json
from flask import Blueprint, jsonify, g, Response
from core.auth import token_required, require_role
from dal.stats_dal import get_platform_stats
from core.errors import ForbiddenError

bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@bp.route("", methods=["GET"])
@token_required
@require_role("administrator")
def get_stats():
    """Restituisce le metriche statistiche aggregate sull'utilizzo della piattaforma (solo Admin)."""

    stats = get_platform_stats()
    return jsonify({
        "status": "success",
        "data": stats
    })


@bp.route("/export", methods=["GET"])
@token_required
@require_role("administrator")
def export_stats():
    """Genera e serve come download un file JSON contenente il dump completo delle statistiche (solo Admin)."""

    stats = get_platform_stats()
    json_data = json.dumps(stats, indent=4, ensure_ascii=False)

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=statistiche_mint.json"}
    )
