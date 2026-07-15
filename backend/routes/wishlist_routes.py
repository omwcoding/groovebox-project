from flask import Blueprint, request, jsonify, g
from core.auth import token_required, require_role
from core.errors import ForbiddenError, BadRequestError, NotFoundError
from dal.wishlist_dal import (
    get_user_wishlist,
    add_to_wishlist,
    delete_from_wishlist,
    find_wishlist_by_id_and_user
)
from dal.copy_dal import insert_copy
from utils.validators import validate_json_payload
from dal.discogs_import_dal import import_album_from_discogs

bp = Blueprint("wishlist", __name__, url_prefix="/api/wishlist")

@bp.route("", methods=["GET"])
@token_required
@require_role("collector")
def get_wishlist_route():
    
    items = get_user_wishlist(g.current_user["id_user"])
    return jsonify({"status": "success", "data": items})

@bp.route("", methods=["POST"])
@token_required
@require_role("collector")
def add_wishlist_route():
        
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
@require_role("collector")
def delete_wishlist_route(wishlist_id):
        
    item = find_wishlist_by_id_and_user(wishlist_id, g.current_user["id_user"])
    if not item:
        raise NotFoundError("Elemento non trovato in wishlist")
        
    delete_from_wishlist(wishlist_id)
    return jsonify({"status": "success", "message": "Elemento rimosso dalla wishlist"})

@bp.route("/<int:wishlist_id>/promote", methods=["POST"])
@token_required
@require_role("collector")
def promote_wishlist_route(wishlist_id):
        
    item = find_wishlist_by_id_and_user(wishlist_id, g.current_user["id_user"])
    if not item:
        raise NotFoundError("Elemento non trovato in wishlist")
        
    data = request.get_json()
    validate_json_payload(data, ["format", "condition"])
    
    format_val = data["format"].strip()
    condition = data["condition"].strip()
    personal_notes = (data.get("personalNotes") or "").strip() or None
    
    # 1. Se l'album non è nel DB locale, importalo ora da Discogs
    id_album = item["id_album"]
    if not id_album and item["discogs_id"]:
        try:
            id_album, _ = import_album_from_discogs(item["discogs_id"], g.current_user["id_user"])
        except Exception as e:
            return jsonify({"status": "error", "message": f"Errore nell'importazione da Discogs: {str(e)}"}), 500
            
    if not id_album:
        raise BadRequestError("Impossibile promuovere elemento senza album locale valido")
        
    # 2. Inserisci la copia fisica
    copy_id = insert_copy(
        format_val=format_val,
        condition=condition,
        personal_notes=personal_notes,
        user_id=g.current_user["id_user"],
        id_album=id_album
    )
    
    # 3. Elimina elemento dalla wishlist
    delete_from_wishlist(wishlist_id)
    
    return jsonify({
        "status": "success",
        "message": "Disco acquistato ed aggiunto al Vault con successo!",
        "data": {"id_copy": copy_id}
    }), 201
