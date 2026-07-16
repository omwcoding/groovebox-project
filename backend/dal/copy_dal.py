"""
GrooveBox - Data Access Layer per Copie Fisiche
===============================================
Gestisce il ciclo di vita e la persistenza delle copie fisiche associate agli 
utenti (physical_copies) nel database PostgreSQL.
"""

import datetime
from core.database import get_db
from dal.album_dal import get_album_artists

def enrich_copy(copy_row):
    """Associa i metadati relativi agli artisti del disco alla copia fisica specificata."""
    if not copy_row:
        return None
    copy_dict = dict(copy_row)
    artists = get_album_artists(copy_dict["id_album"])
    copy_dict["artists"] = [dict(a) for a in artists]
    return copy_dict

def get_user_copies(user_id):
    """Recupera la collezione di copie fisiche di un determinato utente, ordinata per data di aggiunta."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT pc.*, al.title AS album_title, al.release_year, al.genre, al.cover_path
               FROM physical_copies pc
               JOIN albums al ON pc.id_album = al.id_album
               WHERE pc.id_user = %s
               ORDER BY pc.added_date DESC;""",
            (user_id,)
        )
        copies = cursor.fetchall()
        return [enrich_copy(c) for c in copies]
    finally:
        cursor.close()

def find_copy_by_id_and_user(copy_id, user_id):
    """Cerca una specifica copia fisica di proprietà dell'utente indicato."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT pc.*, al.title AS album_title, al.release_year, al.genre, al.cover_path
               FROM physical_copies pc
               JOIN albums al ON pc.id_album = al.id_album
               WHERE pc.id_copy = %s AND pc.id_user = %s;""",
            (copy_id, user_id)
        )
        copy = cursor.fetchone()
        return enrich_copy(copy)
    finally:
        cursor.close()

def insert_copy(id_album, format_val, condition, personal_notes, user_id):
    """Inserisce una nuova copia fisica nella libreria dell'utente."""
    conn = get_db()
    added_date = datetime.date.today().isoformat()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO physical_copies
                   (format, condition, added_date, personal_notes, id_user, id_album)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_copy;""",
                (format_val.strip(), condition.strip(), added_date, personal_notes, user_id, id_album)
            )
            row = cursor.fetchone()
            return row["id_copy"] if row else None

def update_copy_data(copy_id, format_val, condition, personal_notes):
    """Aggiorna le informazioni di una copia fisica nel database."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE physical_copies 
                   SET format = %s, condition = %s, personal_notes = %s 
                   WHERE id_copy = %s;""",
                (format_val.strip(), condition.strip(), personal_notes, copy_id)
            )

def delete_copy_by_id(copy_id):
    """Elimina una copia fisica a partire dal suo identificativo univoco."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM physical_copies WHERE id_copy = %s;", (copy_id,))

def delete_all_copies_by_user(user_id):
    """Elimina tutte le copie fisiche appartenenti all'utente specificato."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM physical_copies WHERE id_user = %s;", (user_id,))
