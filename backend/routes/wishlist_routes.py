from flask import Blueprint, request, jsonify, g
from core.auth import token_required, require_role
from core.errors import ForbiddenError, BadRequestError, NotFoundError
from dal.wishlist_dal import (
    get_user_wishlist,
    add_to_wishlist,
    delete_from_wishlist,
    find_wishlist_by_id_and_user,
    promote_wishlist_item
)
from utils.validators import validate_json_payload

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
    personal_notes = (data.get("personal_notes") or "").strip() or None
    
    try:
        copy_id = promote_wishlist_item(
            wishlist_id=wishlist_id,
            format_val=format_val,
            condition=condition,
            personal_notes=personal_notes,
            user_id=g.current_user["id_user"]
        )
    except ValueError as e:
        raise BadRequestError(str(e))
    except Exception as e:
        return jsonify({"status": "error", "message": f"Errore interno di promozione: {str(e)}"}), 500
        
    return jsonify({
        "status": "success",
        "message": "Disco acquistato ed aggiunto al Vault con successo!",
        "data": {"id_copy": copy_id}
    }), 201
