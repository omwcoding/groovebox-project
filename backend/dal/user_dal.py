from database import get_db

def get_user_by_id(user_id):
    conn = get_db()
    return conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE id_user = ?",
        (user_id,)
    ).fetchone()

def get_user_by_username(username):
    conn = get_db()
    return conn.execute(
        "SELECT * FROM USER WHERE username = ?",
        (username.strip(),)
    ).fetchone()

def get_all_collectors():
    conn = get_db()
    return conn.execute(
        "SELECT id_user, username, name, surname, email, role "
        "FROM USER WHERE role = 'collector' ORDER BY username"
    ).fetchall()

def insert_collector(username, name, surname, email, password_hash):
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
    fields: lista di stringhe es: ['name = ?', 'email = ?']
    values: lista di valori corrispondenti ai placeholders
    """
    conn = get_db()
    query = f"UPDATE USER SET {', '.join(fields)} WHERE id_user = ?"
    with conn:
        conn.execute(query, values + [user_id])
    return get_user_by_id(user_id)

def delete_user_and_transfer_albums(user_id, admin_id=1):
    conn = get_db()
    with conn:
        # Trasferisci la paternità degli album creati all'utente amministratore (id_user = 1)
        conn.execute("UPDATE ALBUM SET id_user = ? WHERE id_user = ?", (admin_id, user_id))
        # Rimuove l'utente. Le copie associate verranno eliminate a cascata (ON DELETE CASCADE)
        conn.execute("DELETE FROM USER WHERE id_user = ?", (user_id,))
