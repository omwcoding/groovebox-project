"""
Mint - Route Blueprint per Amministrazione (V2)
==================================================
Fornisce gli endpoint riservati agli amministratori per la moderazione,
il monitoraggio tecnico, gli insights e la manutenzione della cache.
"""

from flask import Blueprint, request, jsonify, g, current_app
import requests
import datetime
from core.auth import token_required, require_role
from core.errors import BadRequestError, ForbiddenError, NotFoundError
from core.database import get_db
from dal.user_dal import get_all_collectors, get_user_by_id
from dal.report_dal import get_reports, resolve_report_action, get_audit_logs, log_admin_maintenance
from dal.stats_dal import get_platform_stats
from utils.storage import delete_file

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@bp.route("/users", methods=["GET"])
@token_required
@require_role("administrator")
def get_admin_users():
    """Recupera la lista di tutti i collector (incluso lo stato is_banned)."""
    users = get_all_collectors()
    return jsonify({
        "status": "success",
        "data": [dict(u) for u in users]
    })


@bp.route("/users/<int:user_id>/ban", methods=["PUT"])
@token_required
@require_role("administrator")
def toggle_user_ban(user_id):
    """Abilita o disabilita (ban/unban) un utente collector."""
    conn = get_db()
    
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_user, username, role, is_banned FROM users WHERE id_user = %s;", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                raise NotFoundError("Utente non trovato")
                
            if user["role"] == "administrator":
                raise ForbiddenError("Non è possibile modificare lo stato di un amministratore")
                
            new_status = not user["is_banned"]
            cursor.execute("UPDATE users SET is_banned = %s WHERE id_user = %s;", (new_status, user_id))
            
            action = "ban_user" if new_status else "unban_user"
            log_desc = f"Bannato utente '{user['username']}'" if new_status else f"Sbloccato utente '{user['username']}'"
            
            cursor.execute(
                "INSERT INTO admin_audit_logs (id_admin, action_type, target_id, details) VALUES (%s, %s, %s, %s);",
                (g.current_user["id_user"], action, user_id, log_desc)
            )
            
    return jsonify({
        "status": "success",
        "message": f"Stato utente aggiornato con successo. Nuovo stato is_banned: {new_status}",
        "data": {"is_banned": new_status}
    })


@bp.route("/reports", methods=["GET"])
@token_required
@require_role("administrator")
def get_admin_reports():
    """Recupera la lista di tutte le segnalazioni."""
    reports = get_reports()
    return jsonify({
        "status": "success",
        "data": reports
    })


@bp.route("/reports/<int:report_id>/resolve", methods=["PUT"])
@token_required
@require_role("administrator")
def resolve_report(report_id):
    """Risolve una segnalazione applicando il rispettivo provvedimento."""
    data = request.get_json()
    if not data or "action" not in data:
        raise BadRequestError("Azione di risoluzione mancante")
        
    action = data["action"].strip()
    if action not in ["dismiss", "wipe_bio", "wipe_avatar", "ban"]:
        raise BadRequestError("Azione di risoluzione non valida")
        
    try:
        avatar_to_delete = resolve_report_action(report_id, action, g.current_user["id_user"])
        
        # Se l'azione richiedeva la rimozione fisica dell'avatar da Supabase
        if action == "wipe_avatar" and avatar_to_delete:
            try:
                delete_file("avatars", avatar_to_delete)
            except Exception as ex:
                current_app.logger.warning(f"Impossibile eliminare file avatar {avatar_to_delete}: {ex}")
                
        return jsonify({
            "status": "success",
            "message": f"Segnalazione risolta con successo ed applicata azione '{action}'"
        })
    except ValueError as e:
        raise NotFoundError(str(e))


@bp.route("/audit-logs", methods=["GET"])
@token_required
@require_role("administrator")
def get_admin_audit():
    """Recupera la cronologia delle azioni di amministrazione."""
    logs = get_audit_logs()
    return jsonify({
        "status": "success",
        "data": logs
    })


@bp.route("/stats/technical", methods=["GET"])
@token_required
@require_role("administrator")
def get_technical_stats():
    """Recupera i dati di stato del sistema (rate-limit, cache, storage)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Conteggio chiavi in cache
        cursor.execute("SELECT COUNT(*) AS total FROM discogs_cache;")
        cache_row = cursor.fetchone()
        cache_count = cache_row["total"] if cache_row else 0
        
        # Conteggio file memorizzati per categoria (stima storage)
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE avatar_path IS NOT NULL;")
        avatar_row = cursor.fetchone()
        avatar_files = avatar_row["total"] if avatar_row else 0
        
        cursor.execute("SELECT COUNT(*) AS total FROM albums WHERE cover_path IS NOT NULL;")
        cover_row = cursor.fetchone()
        cover_files = cover_row["total"] if cover_row else 0
        
        cursor.execute("SELECT COUNT(*) AS total FROM artists WHERE image_path IS NOT NULL;")
        artist_row = cursor.fetchone()
        artist_files = artist_row["total"] if artist_row else 0
    finally:
        cursor.close()
        
    # Interroga il rate limit di Discogs effettuando una richiesta leggera all'endpoint radice
    discogs_limit = 60
    discogs_remaining = 60
    try:
        from utils.discogs import _get_headers
        res = requests.get("https://api.discogs.com/", headers=_get_headers(), timeout=3)
        if res.status_code == 200:
            discogs_limit = int(res.headers.get("X-Discogs-Ratelimit-Limit", 60))
            discogs_remaining = int(res.headers.get("X-Discogs-Ratelimit-Remaining", 60))
    except Exception:
        pass
        
    return jsonify({
        "status": "success",
        "data": {
            "discogs_api": {
                "limit": discogs_limit,
                "remaining": discogs_remaining
            },
            "cache": {
                "total_entries": cache_count
            },
            "storage_files": {
                "avatars": avatar_files,
                "covers": cover_files,
                "artists": artist_files,
                "total_files": avatar_files + cover_files + artist_files
            }
        }
    })


@bp.route("/stats/business", methods=["GET"])
@token_required
@require_role("administrator")
def get_business_stats():
    """Recupera le statistiche di utilizzo della piattaforma e di mercato."""
    stats = get_platform_stats()
    return jsonify({
        "status": "success",
        "data": stats
    })


@bp.route("/users/<int:user_id>/wipe-avatar", methods=["PUT"])
@token_required
@require_role("administrator")
def admin_wipe_avatar(user_id):
    """Azzera l'avatar_path dell'utente specificato ed elimina fisicamente il file da Supabase Storage."""
    conn = get_db()
    avatar_to_delete = None
    
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_user, username, avatar_path FROM users WHERE id_user = %s;", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise NotFoundError("Utente non trovato")
                
            avatar_to_delete = user["avatar_path"]
            cursor.execute("UPDATE users SET avatar_path = NULL WHERE id_user = %s;", (user_id,))
            
            # Audit log
            cursor.execute(
                "INSERT INTO admin_audit_logs (id_admin, action_type, target_id, details) VALUES (%s, %s, %s, %s);",
                (g.current_user["id_user"], "wipe_user_avatar", user_id, f"Rimosso avatar di @{user['username']} per moderazione")
            )
            
    # Elimina da Supabase Storage
    if avatar_to_delete:
        try:
            delete_file("avatars", avatar_to_delete)
        except Exception as ex:
            current_app.logger.warning(f"Impossibile eliminare file avatar {avatar_to_delete}: {ex}")
            
    return jsonify({
        "status": "success",
        "message": "Foto profilo rimossa con successo"
    })


@bp.route("/users/<int:user_id>/wipe-bio", methods=["PUT"])
@token_required
@require_role("administrator")
def admin_wipe_bio(user_id):
    """Azzera la biografia dell'utente specificato."""
    conn = get_db()
    
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_user, username FROM users WHERE id_user = %s;", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise NotFoundError("Utente non trovato")
                
            cursor.execute("UPDATE users SET bio = NULL WHERE id_user = %s;", (user_id,))
            
            # Audit log
            cursor.execute(
                "INSERT INTO admin_audit_logs (id_admin, action_type, target_id, details) VALUES (%s, %s, %s, %s);",
                (g.current_user["id_user"], "wipe_user_bio", user_id, f"Azzerata biografia di @{user['username']} per moderazione")
            )
            
    return jsonify({
        "status": "success",
        "message": "Biografia azzerata con successo"
    })


@bp.route("/maintenance/refresh-expired-cache", methods=["POST"])
@token_required
@require_role("administrator")
def refresh_cache():
    """Rimuove dalla cache locale le risposte di Discogs più vecchie di 30 giorni."""
    conn = get_db()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
    
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM discogs_cache WHERE cached_at < %s;", (cutoff,))
            deleted_count = cursor.rowcount
            
            log_admin_maintenance(
                g.current_user["id_user"],
                "refresh_cache",
                None,
                f"Pulizia cache Discogs eseguita: rimossi {deleted_count} elementi obsoleti"
            )
            
    return jsonify({
        "status": "success",
        "message": f"Pulizia completata con successo. Rimossi {deleted_count} elementi obsoleti."
    })


@bp.route("/maintenance/manual-entry/<int:album_id>", methods=["DELETE"])
@token_required
@require_role("administrator")
def delete_manual_entry(album_id):
    """Consente all'amministratore di rimuovere un inserimento album manuale errato o non idoneo."""
    conn = get_db()
    
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_album, title, discogs_id FROM albums WHERE id_album = %s;", (album_id,))
            album = cursor.fetchone()
            
            if not album:
                raise NotFoundError("Album non trovato")
                
            if album["discogs_id"] is not None:
                raise BadRequestError("Non è consentito eliminare album ufficiali importati da Discogs")
                
            # Cancella a cascata (physical_copies e wishlists legati a questo album si cancellano via cascade del DB)
            cursor.execute("DELETE FROM albums WHERE id_album = %s;", (album_id,))
            
            log_admin_maintenance(
                g.current_user["id_user"],
                "delete_manual_album",
                album_id,
                f"Eliminato album manuale inappropriato '{album['title']}' (ID: {album_id})"
            )
            
    return jsonify({
        "status": "success",
        "message": f"Album manuale '{album['title']}' rimosso con successo dal catalogo."
    })
