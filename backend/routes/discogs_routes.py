"""
GrooveBox - Route Blueprint per integrazione Discogs
===================================================
Fornisce gli endpoint per cercare album/artisti su Discogs ed importarli
automaticamente nel catalogo locale scaricandone copertine, tracklist e dettagli.
"""

from flask import Blueprint, request, jsonify, g, current_app
from core.auth import token_required, require_role
from core.errors import BadRequestError, ForbiddenError, NotFoundError
from utils.discogs import (
    search_releases,
    search_artists,
    get_release,
    get_artist,
    download_discogs_image
)
from dal.album_dal import insert_album, enrich_album, search_albums_local
from dal.artist_dal import (
    find_artist_by_discogs_id,
    find_artist_by_name,
    insert_artist,
    update_artist_discogs_info
)
from dal.discogs_import_dal import import_album_from_discogs
from core.database import get_db
import os
import uuid

bp = Blueprint("discogs", __name__, url_prefix="/api/discogs")



@bp.route("/search/artist", methods=["GET"])
@token_required
def search_artist_route():
    """Cerca artisti su Discogs."""
    query = request.args.get("q", "").strip()
    if not query:
        raise BadRequestError("Parametro di ricerca 'q' mancante")
    
    try:
        results = search_artists(query)
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/search/unified", methods=["GET"])
@token_required
def search_unified_route():
    """Ricerca unificata (locale + Discogs)."""
    query = request.args.get("q", "").strip()
    if not query:
        raise BadRequestError("Parametro di ricerca 'q' mancante")
    
    local_albums = search_albums_local(query, limit=10)
    
    local_results = []
    local_discogs_ids = set()
    for album in local_albums:
        if album:
            album["source"] = "local"
            local_results.append(album)
            if album.get("discogs_id"):
                local_discogs_ids.add(album["discogs_id"])
                
    discogs_results = []
    try:
        discogs_raw = search_releases(query, limit=10)
        for r in discogs_raw:
            if r.get("discogs_id") not in local_discogs_ids:
                r["source"] = "discogs"
                discogs_results.append(r)
    except Exception:
        pass
        
    return jsonify({
        "status": "success",
        "data": local_results + discogs_results
    })

@bp.route("/import/album", methods=["POST"])
@token_required
@require_role("collector", "administrator")
def import_album_route():
    """
    Importa un album da Discogs nel catalogo globale.
    Crea automaticamente l'artista/i se non presenti e ne scarica biografia/foto.
    Scarica la copertina e salva la tracklist.
    """
        
    data = request.get_json()
    if not data or "discogs_id" not in data:
        raise BadRequestError("Parametro 'discogs_id' mancante")
        
    discogs_id = int(data["discogs_id"])
    
    try:
        album_id, was_existing = import_album_from_discogs(discogs_id, g.current_user["id_user"])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    conn = get_db()
    album_row = conn.execute(
        "SELECT al.*, us.username AS creator_username "
        "FROM ALBUM al "
        "LEFT JOIN USER us ON al.id_user = us.id_user "
        "WHERE al.id_album = ?",
        (album_id,)
    ).fetchone()

    if was_existing:
        return jsonify({
            "status": "success",
            "message": "Album già presente a catalogo",
            "data": enrich_album(album_row)
        }), 200
    else:
        return jsonify({
            "status": "success",
            "message": "Album importato con successo da Discogs",
            "data": enrich_album(album_row)
        }), 201

@bp.route("/import/artist", methods=["POST"])
@token_required
@require_role("collector", "administrator")
def import_artist_route():
    """
    Importa o aggiorna un artista da Discogs nel database locale.
    Scarica la foto e la biografia.
    """
        
    data = request.get_json()
    if not data or "discogs_id" not in data:
        raise BadRequestError("Parametro 'discogs_id' mancante")
        
    discogs_id = int(data["discogs_id"])
    
    # Controlla se esiste già l'artista
    local_art = find_artist_by_discogs_id(discogs_id)
    
    try:
        art_details = get_artist(discogs_id)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Errore nel recupero dell'artista da Discogs: {str(e)}"}), 500

    bio = art_details.get("biography", "")
    photo_url = art_details.get("photo_url")
    photo_filename = None
    
    # Se esiste già, aggiorniamo le sue info
    if local_art:
        art_id = local_art["id_artist"]
        photo_filename = local_art["image_path"]
        
        # Se ha una nuova foto ed era vuoto o vogliamo scaricarlo
        if photo_url and not photo_filename:
            try:
                photo_ext = "jpg"
                photo_filename = f"artist_discogs_{discogs_id}.{photo_ext}"
                dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
                if not os.path.exists(dest):
                    download_discogs_image(photo_url, dest)
            except Exception as e:
                current_app.logger.warning(f"Impossibile scaricare foto artista: {e}")
                
        update_artist_discogs_info(art_id, discogs_id, bio, photo_filename)
        
        # Recupera aggiornato
        conn = get_db()
        updated = conn.execute("SELECT * FROM ARTIST WHERE id_artist = ?", (art_id,)).fetchone()
        return jsonify({
            "status": "success",
            "message": "Artista aggiornato con successo con dati Discogs",
            "data": dict(updated)
        }), 200
        
    # Se non esiste per discogs_id, controlla se c'è per nome
    local_art_name = find_artist_by_name(art_details["name"])
    if local_art_name:
        art_id = local_art_name["id_artist"]
        photo_filename = local_art_name["image_path"]
        
        if photo_url and not photo_filename:
            try:
                photo_ext = "jpg"
                photo_filename = f"artist_discogs_{discogs_id}.{photo_ext}"
                dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
                if not os.path.exists(dest):
                    download_discogs_image(photo_url, dest)
            except Exception as e:
                current_app.logger.warning(f"Impossibile scaricare foto artista: {e}")
                
        update_artist_discogs_info(art_id, discogs_id, bio, photo_filename)
        
        conn = get_db()
        updated = conn.execute("SELECT * FROM ARTIST WHERE id_artist = ?", (art_id,)).fetchone()
        return jsonify({
            "status": "success",
            "message": "Artista collegato ed aggiornato con successo con dati Discogs",
            "data": dict(updated)
        }), 200
        
    # Altrimenti crea un nuovo record
    if photo_url:
        try:
            photo_ext = "jpg"
            photo_filename = f"artist_discogs_{discogs_id}.{photo_ext}"
            dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
            if not os.path.exists(dest):
                download_discogs_image(photo_url, dest)
        except Exception as e:
            current_app.logger.warning(f"Impossibile scaricare foto artista: {e}")
            
    art_id = insert_artist(art_details["name"], discogs_id, bio, photo_filename)
    
    conn = get_db()
    new_art = conn.execute("SELECT * FROM ARTIST WHERE id_artist = ?", (art_id,)).fetchone()
    return jsonify({
        "status": "success",
        "message": "Artista importato con successo da Discogs",
        "data": dict(new_art)
    }), 201
