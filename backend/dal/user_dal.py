"""
GrooveBox - Data Access Layer per Utenti
=========================================
Gestisce le operazioni di lettura, scrittura, aggiornamento e rimozione
delle anagrafiche utente (USER) nel database.
"""

from core.database import get_db

def get_user_by_id(user_id):
    """Cerca un utente per identificativo univoco, escludendo l'hash della password."""
    conn = get_db()
    return conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE id_user = ?",
        (user_id,)
    ).fetchone()

def get_user_by_username(username):
    """Cerca un utente per username, includendo tutti i campi del record."""
    conn = get_db()
    return conn.execute(
        "SELECT * FROM USER WHERE username = ?",
        (username.strip(),)
    ).fetchone()

def get_all_collectors():
    """Recupera l'elenco di tutti gli utenti registrati con ruolo 'collector'."""
    conn = get_db()
    return conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE role = 'collector' ORDER BY username"
    ).fetchall()

def insert_collector(username, name, surname, email, password_hash):
    """Crea un nuovo profilo utente con ruolo predefinito 'collector'."""
    conn = get_db()
    with conn:
        cursor = conn.execute(
            "INSERT INTO USER (username, name, surname, email, passwordHash, role) "
            "VALUES (?, ?, ?, ?, ?, 'collector')",
            (username, name, surname, email, password_hash)
        )
        return cursor.lastrowid

def update_user_profile(user_id, fields, values):
    """
    Aggiorna i dati anagrafici del profilo utente specificato.
    
    Per prevenire vulnerabilità SQL Injection, l'argomento 'fields' deve contenere 
    esclusivamente identificatori di colonna statici definiti dall'applicazione, 
    mentre i dati dinamici devono essere passati tramite l'argomento 'values'.
    """
    conn = get_db()
    query = f"UPDATE USER SET {', '.join(fields)} WHERE id_user = ?"
    with conn:
        conn.execute(query, values + [user_id])
    return get_user_by_id(user_id)

def delete_user_and_keep_albums(user_id):
    """
    Elimina un utente dal sistema preservando gli album da lui inseriti 
    (impostando l'attributo id_user a NULL). Le copie fisiche collegate 
    all'utente vengono eliminate a cascata.
    """
    conn = get_db()
    with conn:
        conn.execute("UPDATE ALBUM SET id_user = NULL WHERE id_user = ?", (user_id,))
        conn.execute("DELETE FROM USER WHERE id_user = ?", (user_id,))

