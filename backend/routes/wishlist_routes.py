from flask import Blueprint, request, jsonify, g
from core.auth import token_required
from core.errors import ForbiddenError, BadRequestError, NotFoundError
from dal.wishlist_dal import (
    get_user_wishlist,
    add_to_wishlist,
    delete_from_wishlist,
    find_wishlist_by_id_and_user
)
from dal.copy_dal import insert_copy
from utils.validators import validate_json_payload
from utils.discogs import get_release, get_artist
from dal.album_dal import enrich_album
from dal.artist_dal import find_artist_by_discogs_id, find_artist_by_name, insert_artist
from core.database import get_db

bp = Blueprint("wishlist", __name__, url_prefix="/api/wishlist")

@bp.route("", methods=["GET"])
@token_required
def get_wishlist_route():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")
    
    items = get_user_wishlist(g.current_user["id_user"])
    return jsonify({"status": "success", "data": items})

@bp.route("", methods=["POST"])
@token_required
def add_wishlist_route():
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")
        
    data = request.get_json()
    if not data:
        raise BadRequestError("Nessun dato fornito")
        
    id_album = data.get("id_album")
    discogs_id = data.get("discogs_id")
    title = data.get("title")
    artist_name = data.get("artist_name")
    cover_url = data.get("cover_url")
    
    if not id_album and not discogs_id:
        raise BadRequestError("Fornire id_album o discogs_id")
        
    wishlist_id = add_to_wishlist(
        user_id=g.current_user["id_user"],
        id_album=id_album,
        discogs_id=discogs_id,
        title=title,
        artist_name=artist_name,
        cover_url=cover_url
    )
    
    return jsonify({
        "status": "success",
        "message": "Album aggiunto alla wishlist con successo",
        "data": {"id_wishlist": wishlist_id}
    }), 201

@bp.route("/<int:wishlist_id>", methods=["DELETE"])
@token_required
def delete_wishlist_route(wishlist_id):
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")
        
    item = find_wishlist_by_id_and_user(wishlist_id, g.current_user["id_user"])
    if not item:
        raise NotFoundError("Elemento non trovato in wishlist")
        
    delete_from_wishlist(wishlist_id)
    return jsonify({"status": "success", "message": "Elemento rimosso dalla wishlist"})

@bp.route("/<int:wishlist_id>/promote", methods=["POST"])
@token_required
def promote_wishlist_route(wishlist_id):
    if g.current_user["role"] != "collector":
        raise ForbiddenError("Accesso riservato ai Collector")
        
    item = find_wishlist_by_id_and_user(wishlist_id, g.current_user["id_user"])
    if not item:
        raise NotFoundError("Elemento non trovato in wishlist")
        
    data = request.get_json()
    validate_json_payload(data, ["format", "condition"])
    
    format_val = data["format"].strip()
    condition = data["condition"].strip()
    personal_notes = data.get("personalNotes", "").strip() or None
    
    conn = get_db()
    
    # 1. Se l'album non è nel DB locale, importalo ora da Discogs
    id_album = item["id_album"]
    if not id_album and item["discogs_id"]:
        discogs_id = item["discogs_id"]
        # Controlla se qualcun altro lo ha importato nel frattempo
        existing = conn.execute("SELECT id_album FROM ALBUM WHERE discogs_id = ?", (discogs_id,)).fetchone()
        if existing:
            id_album = existing[0]
        else:
            # Importa da Discogs
            release_info = get_release(discogs_id)
            
            # Artisti
            local_artist_ids = []
            for art in release_info["artists"]:
                art_discogs_id = art["discogs_id"]
                art_name = art["name"]
                
                local_art = find_artist_by_discogs_id(art_discogs_id)
                if not local_art:
                    local_art = find_artist_by_name(art_name)
                    
                if local_art:
                    art_id = local_art["id_artist"]
                else:
                    # Crea artista e importa biografia/foto in background
                    try:
                        art_details = get_artist(art_discogs_id)
                        bio = art_details.get("biography")
                        photo_url = art_details.get("photo_url")
                    except Exception:
                        bio = None
                        photo_url = None
                    
                    art_image_path = None
                    if photo_url:
                        import uuid
                        import os
                        from flask import current_app
                        from utils.discogs import download_discogs_image
                        filename = f"artist_{uuid.uuid4().hex}.jpg"
                        filepath = os.path.join(current_app.config["ARTISTS_FOLDER"], filename)
                        if download_discogs_image(photo_url, filepath):
                            art_image_path = filename
                    
                    art_id = insert_artist(art_name, art_discogs_id, bio, art_image_path)
                local_artist_ids.append(art_id)
            
            # Scarica copertina
            cover_path = None
            if release_info["cover_url"]:
                import uuid
                import os
                from flask import current_app
                from utils.discogs import download_discogs_image
                filename = f"cover_{uuid.uuid4().hex}.jpg"
                filepath = os.path.join(current_app.config["COVERS_FOLDER"], filename)
                if download_discogs_image(release_info["cover_url"], filepath):
                    cover_path = filename
            
            from dal.album_dal import insert_album
            id_album = insert_album(
                title=release_info["title"],
                release_year=release_info["release_year"],
                genre=release_info["genre"],
                artist_ids=local_artist_ids,
                creator_user_id=g.current_user["id_user"],
                discogs_id=discogs_id,
                tracklist=release_info["tracklist"],
                cover_path=cover_path,
                label=release_info["label"],
                catno=release_info["catno"],
                barcode=release_info["barcode"],
                country=release_info["country"]
            )
            
    if not id_album:
        raise BadRequestError("Impossibile promuovere elemento senza album locale valido")
        
    # 2. Inserisci la copia fisica
    copy_id = insert_copy(
        format_val=format_val,
        condition=condition,
        personal_notes=personal_notes,
        user_id=g.current_user["id_user"],
        album_id=id_album
    )
    
    # 3. Elimina elemento dalla wishlist
    delete_from_wishlist(wishlist_id)
    
    return jsonify({
        "status": "success",
        "message": "Disco acquistato ed aggiunto al Vault con successo!",
        "data": {"id_copy": copy_id}
    }), 201
