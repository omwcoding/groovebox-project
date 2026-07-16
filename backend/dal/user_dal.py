"""
GrooveBox - Data Access Layer per Utenti
=========================================
Gestisce le operazioni di lettura, scrittura, aggiornamento e rimozione
delle anagrafiche utente (users) nel database PostgreSQL.
"""

from core.database import get_db

def get_user_by_id(user_id):
    """Cerca un utente per identificativo univoco, escludendo l'hash della password."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id_user, username, name, surname, email, role, is_public, bio, avatar_path "
            "FROM users WHERE id_user = %s;",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()

def get_user_by_username(username):
    """Cerca un utente per username, includendo tutti i campi del record."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username = %s;",
            (username.strip(),)
        )
        return cursor.fetchone()
    finally:
        cursor.close()

def get_all_collectors():
    """Recupera l'elenco di tutti gli utenti registrati con ruolo 'collector'."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id_user, username, name, surname, email, role "
            "FROM users WHERE role = 'collector' ORDER BY username;"
        )
        return cursor.fetchall()
    finally:
        cursor.close()

def insert_collector(username, name, surname, email, password_hash):
    """Crea un nuovo profilo utente con ruolo predefinito 'collector'."""
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, name, surname, email, password_hash, role) "
                "VALUES (%s, %s, %s, %s, %s, 'collector') RETURNING id_user;",
                (username, name, surname, email, password_hash)
            )
            row = cursor.fetchone()
            return row["id_user"] if row else None

def update_user_profile(user_id, fields, values):
    """
    Aggiorna i dati anagrafici del profilo utente specificato.
    
    Per prevenire vulnerabilità SQL Injection, l'argomento 'fields' deve contenere 
    esclusivamente identificatori di colonna statici definiti dall'applicazione, 
    mentre i dati dinamici devono essere passati tramite l'argomento 'values'.
    """
    conn = get_db()
    query = f"UPDATE users SET {', '.join(fields)} WHERE id_user = %s;"
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(query, values + [user_id])
    return get_user_by_id(user_id)

def delete_user_and_keep_albums(user_id):
    """
    Elimina un utente dal sistema preservando gli album da lui inseriti 
    (impostando l'attributo id_user a NULL). Le copie fisiche collegate 
    all'utente vengono eliminate a cascata.
    """
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE albums SET id_user = NULL WHERE id_user = %s;", (user_id,))
            cursor.execute("DELETE FROM users WHERE id_user = %s;", (user_id,))

def get_user_public_profile(username):
    """
    Recupera il profilo pubblico di un collector tramite username.
    Ritorna None se l'utente non esiste, non è un collector, o ha is_public = 0.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id_user, username, name, surname, bio, avatar_path "
            "FROM users WHERE username = %s AND role = 'collector' AND is_public = TRUE;",
            (username,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()

def get_user_stats(user_id):
    """Recupera il conteggio delle copie fisiche e degli album inseriti da un utente."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM physical_copies WHERE id_user = %s;", (user_id,))
        row_copies = cursor.fetchone()
        copies_count = row_copies["total"] if row_copies else 0

        cursor.execute("SELECT COUNT(*) AS total FROM albums WHERE id_user = %s;", (user_id,))
        row_albums = cursor.fetchone()
        albums_count = row_albums["total"] if row_albums else 0

        return {
            "copies_count": copies_count,
            "albums_count": albums_count
        }
    finally:
        cursor.close()
