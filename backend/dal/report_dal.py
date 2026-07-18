"""
Mint - Data Access Layer per Segnalazioni (Reports) e Audit Logs
==================================================================
Gestisce le operazioni di lettura e scrittura relative alle segnalazioni dei profili 
e al registro delle attività degli amministratori (Audit Logs).
"""

from core.database import get_db
import datetime

def add_report(reporter_id, reported_id, category, details):
    """Crea una nuova segnalazione di profilo utente."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO reports (id_reporter, id_reported, category, details, status) "
                "VALUES (%s, %s, %s, %s, 'pending') RETURNING id_report;",
                (reporter_id, reported_id, category.strip(), details.strip() if details else None)
            )
            row = cursor.fetchone()
            return row["id_report"] if row else None


def get_reports():
    """Recupera l'elenco di tutte le segnalazioni inserite, arricchite con gli username, bio e avatar."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT r.id_report, r.id_reporter, r.id_reported, r.category, r.details, r.status, r.created_at, r.resolved_at,
                   u1.username AS reporter_username, u2.username AS reported_username,
                   u2.bio AS reported_bio, u2.avatar_path AS reported_avatar_path
            FROM reports r
            JOIN users u1 ON r.id_reporter = u1.id_user
            JOIN users u2 ON r.id_reported = u2.id_user
            ORDER BY r.created_at DESC;
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()


def find_report_by_id(report_id):
    """Cerca una segnalazione specifica tramite ID."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT r.*, u1.username AS reporter_username, u2.username AS reported_username,
                   u2.bio AS reported_bio, u2.avatar_path AS reported_avatar_path
            FROM reports r
            JOIN users u1 ON r.id_reporter = u1.id_user
            JOIN users u2 ON r.id_reported = u2.id_user
            WHERE r.id_report = %s;
            """,
            (report_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()


def resolve_report_action(report_id, action, admin_id):
    """
    Risolve una segnalazione applicando il rispettivo provvedimento 
    e registrando l'azione nell'Audit Log all'interno di una transazione SQL.
    Ritorna l'eventuale nome del file avatar rimosso (se applicabile).
    """
    conn = get_db()
    avatar_to_delete = None
    
    with conn:
        with conn.cursor() as cursor:
            # 1. Recupera dettagli segnalazione ed username dell'utente segnalato
            cursor.execute(
                """
                SELECT r.id_reported, u.username, u.avatar_path
                FROM reports r
                JOIN users u ON r.id_reported = u.id_user
                WHERE r.id_report = %s;
                """,
                (report_id,)
            )
            reported_info = cursor.fetchone()
            if not reported_info:
                raise ValueError("Segnalazione non trovata")
                
            reported_user_id = reported_info["id_reported"]
            reported_username = reported_info["username"]
            avatar_path = reported_info["avatar_path"]

            # 2. Applica la sanzione selezionata
            status = "resolved"
            details_log = f"Risolta segnalazione #{report_id} su utente {reported_username}: "

            if action == "dismiss":
                status = "dismissed"
                details_log += "segnalazione archiviata senza provvedimenti."
                
            elif action == "wipe_bio":
                cursor.execute("UPDATE users SET bio = NULL WHERE id_user = %s;", (reported_user_id,))
                details_log += "biografia azzerata."
                
            elif action == "wipe_avatar":
                if avatar_path:
                    avatar_to_delete = avatar_path
                cursor.execute("UPDATE users SET avatar_path = NULL WHERE id_user = %s;", (reported_user_id,))
                details_log += "avatar rimosso."
                
            elif action == "ban":
                cursor.execute("UPDATE users SET is_banned = TRUE WHERE id_user = %s;", (reported_user_id,))
                details_log += "account bannato/sospeso."
                # Risolve automaticamente tutti gli altri report pendenti dello stesso utente
                resolved_at = datetime.datetime.now()
                cursor.execute(
                    "UPDATE reports SET status = 'resolved', resolved_at = %s WHERE id_reported = %s AND status = 'pending' AND id_report != %s;",
                    (resolved_at, reported_user_id, report_id)
                )
            else:
                raise ValueError("Azione di moderazione non valida")

            # 3. Aggiorna lo stato del report
            resolved_at = datetime.datetime.now()
            cursor.execute(
                "UPDATE reports SET status = %s, resolved_at = %s WHERE id_report = %s;",
                (status, resolved_at, report_id)
            )

            # 4. Registra l'azione nell'audit log
            cursor.execute(
                "INSERT INTO admin_audit_logs (id_admin, action_type, target_id, details) "
                "VALUES (%s, %s, %s, %s);",
                (admin_id, f"resolve_report_{action}", report_id, details_log)
            )
            
    return avatar_to_delete


def get_audit_logs():
    """Recupera l'elenco di tutte le attività amministrative registrate."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT l.id_log, l.id_admin, l.action_type, l.target_id, l.details, l.created_at,
                   u.username AS admin_username
            FROM admin_audit_logs l
            JOIN users u ON l.id_admin = u.id_user
            ORDER BY l.created_at DESC;
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()


def log_admin_maintenance(admin_id, action_type, target_id, details):
    """Registra un'azione di manutenzione del catalogo/cache nell'audit log."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO admin_audit_logs (id_admin, action_type, target_id, details) "
                "VALUES (%s, %s, %s, %s);",
                (admin_id, action_type, target_id, details)
            )
