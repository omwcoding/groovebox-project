"""
GrooveBox - Route Blueprint per integrazione Discogs
===================================================
Fornisce gli endpoint per cercare album/artisti su Discogs ed importarli
automaticamente nel catalogo locale scaricandone copertine, tracklist e dettagli.
"""

from flask import Blueprint, request, jsonify, g, current_app
from core.auth import token_required
from core.errors import BadRequestError, ForbiddenError, NotFoundError
from utils.discogs import (
    search_releases,
    search_artists,
    get_release,
    get_artist,
    download_discogs_image
)
from dal.album_dal import insert_album, enrich_album
from dal.artist_dal import (
    find_artist_by_discogs_id,
    find_artist_by_name,
    insert_artist,
    update_artist_discogs_info
)
from core.database import get_db
import os
import uuid

bp = Blueprint("discogs", __name__, url_prefix="/api/discogs")

@bp.route("/search/album", methods=["GET"])
@token_required
def search_album_route():
    """Cerca album/release su Discogs."""
    query = request.args.get("q", "").strip()
    if not query:
        raise BadRequestError("Parametro di ricerca 'q' mancante")
    
    try:
        results = search_releases(query)
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    
    conn = get_db()
    local_rows = conn.execute(
        """SELECT DISTINCT al.* 
           FROM ALBUM al
           LEFT JOIN ALBUM_ARTIST aa ON al.id_album = aa.id_album
           LEFT JOIN ARTIST ar ON aa.id_artist = ar.id_artist
           WHERE al.title LIKE ? OR ar.name LIKE ?
           LIMIT 10""",
        (f"%{query}%", f"%{query}%")
    ).fetchall()
    
    local_results = []
    local_discogs_ids = set()
    for row in local_rows:
        enriched = enrich_album(row)
        if enriched:
            enriched["source"] = "local"
            local_results.append(enriched)
            if enriched.get("discogs_id"):
                local_discogs_ids.add(enriched["discogs_id"])
                
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
def import_album_route():
    """
    Importa un album da Discogs nel catalogo globale.
    Crea automaticamente l'artista/i se non presenti e ne scarica biografia/foto.
    Scarica la copertina e salva la tracklist.
    """
    role = g.current_user["role"]
    if role not in ("collector", "administrator"):
        raise ForbiddenError("Solo i Collector e gli Amministratori possono importare album")
        
    data = request.get_json()
    if not data or "discogs_id" not in data:
        raise BadRequestError("Parametro 'discogs_id' mancante")
        
    discogs_id = int(data["discogs_id"])
    
    # 1. Controlla se l'album è già importato
    conn = get_db()
    existing_album = conn.execute(
        "SELECT al.*, us.username AS creator_username "
        "FROM ALBUM al "
        "LEFT JOIN USER us ON al.id_user = us.id_user "
        "WHERE al.discogs_id = ?",
        (discogs_id,)
    ).fetchone()
    
    if existing_album:
        # Se è già presente nel DB locale, restituiscilo direttamente
        return jsonify({
            "status": "success",
            "message": "Album già presente a catalogo",
            "data": enrich_album(existing_album)
        }), 200
        
    try:
        # 2. Recupera dettagli release da Discogs
        release_info = get_release(discogs_id)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Errore nel recupero della release da Discogs: {str(e)}"}), 500

    # 3. Risoluzione ed importazione degli artisti della release
    local_artist_ids = []
    for art in release_info["artists"]:
        art_discogs_id = art["discogs_id"]
        art_name = art["name"]
        
        # Cerca artista locale per ID Discogs
        local_art = find_artist_by_discogs_id(art_discogs_id)
        
        # Se non lo trova, prova per nome
        if not local_art:
            local_art = find_artist_by_name(art_name)
            
        if local_art:
            # Artista esistente
            art_id = local_art["id_artist"]
            # Se l'artista esistente non ha ancora le info Discogs collegate, le arricchiamo ora
            if not local_art["discogs_id"] or not local_art["biography"]:
                try:
                    art_details = get_artist(art_discogs_id)
                    bio = art_details.get("biography", "")
                    photo_url = art_details.get("photo_url")
                    photo_filename = None
                    
                    if photo_url:
                        photo_ext = "jpg"
                        photo_filename = f"artist_discogs_{art_discogs_id}.{photo_ext}"
                        dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
                        if not os.path.exists(dest):
                            download_discogs_image(photo_url, dest)
                        
                    update_artist_discogs_info(art_id, art_discogs_id, bio, photo_filename)
                except Exception as ex:
                    # Non bloccante per l'importazione dell'album
                    current_app.logger.warning(f"Impossibile arricchire l'artista {art_name}: {ex}")
            
            local_artist_ids.append(art_id)
        else:
            # Artista non presente: lo creiamo recuperando i dettagli completi da Discogs
            try:
                art_details = get_artist(art_discogs_id)
                bio = art_details.get("biography", "")
                photo_url = art_details.get("photo_url")
                photo_filename = None
                
                if photo_url:
                    photo_ext = "jpg"
                    photo_filename = f"artist_discogs_{art_discogs_id}.{photo_ext}"
                    dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
                    if not os.path.exists(dest):
                        download_discogs_image(photo_url, dest)
                    
                art_id = insert_artist(art_name, art_discogs_id, bio, photo_filename)
                local_artist_ids.append(art_id)
            except Exception as ex:
                # Fallback: crea l'artista solo col nome
                current_app.logger.warning(f"Errore caricamento dettagli artista {art_name}, uso fallback nome: {ex}")
                art_id = insert_artist(art_name, art_discogs_id)
                local_artist_ids.append(art_id)
                
    if not local_artist_ids:
        # Se non ci sono artisti nella release, inseriamo a nome di un artista ignoto
        unknown_art = find_artist_by_name("Unknown Artist")
        if unknown_art:
            local_artist_ids.append(unknown_art["id_artist"])
        else:
            art_id = insert_artist("Unknown Artist")
            local_artist_ids.append(art_id)

    # 4. Scarica la copertina
    cover_filename = None
    cover_url = release_info["cover_url"]
    if cover_url:
        try:
            # Riconosci l'estensione, di solito jpg o png da Discogs
            ext = "jpg"
            if ".png" in cover_url.lower():
                ext = "png"
            elif ".webp" in cover_url.lower():
                ext = "webp"
                
            cover_filename = f"album_discogs_{discogs_id}.{ext}"
            dest_cover = os.path.join(current_app.config["COVERS_FOLDER"], cover_filename)
            if not os.path.exists(dest_cover):
                download_discogs_image(cover_url, dest_cover)
        except Exception as e:
            current_app.logger.warning(f"Impossibile scaricare copertina da Discogs: {e}")

    # 5. Salva l'album nel DB locale
    try:
        album_id = insert_album(
            title=release_info["title"],
            release_year=release_info["release_year"],
            genre=release_info["genre"],
            artist_ids=local_artist_ids,
            creator_user_id=g.current_user["id_user"],
            discogs_id=discogs_id,
            tracklist=release_info["tracklist"],
            cover_path=cover_filename,
            label=release_info.get("label"),
            catno=release_info.get("catno"),
            barcode=release_info.get("barcode"),
            country=release_info.get("country")
        )
        
        # Recupera il record inserito per restituirlo
        album_row = conn.execute(
            "SELECT al.*, us.username AS creator_username "
            "FROM ALBUM al "
            "LEFT JOIN USER us ON al.id_user = us.id_user "
            "WHERE al.id_album = ?",
            (album_id,)
        ).fetchone()
        
        return jsonify({
            "status": "success",
            "message": "Album importato con successo da Discogs",
            "data": enrich_album(album_row)
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Errore durante il salvataggio locale dell'album: {str(e)}"}), 500

@bp.route("/import/artist", methods=["POST"])
@token_required
def import_artist_route():
    """
    Importa o aggiorna un artista da Discogs nel database locale.
    Scarica la foto e la biografia.
    """
    role = g.current_user["role"]
    if role not in ("collector", "administrator"):
        raise ForbiddenError("Non autorizzato")
        
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
