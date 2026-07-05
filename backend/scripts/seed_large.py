"""
GrooveBox - Script di Popolamento Database Large (Seeding)
===========================================================
Crea:
  - 50 Collector (Utenti)
  - 60 Artisti
  - 120 Album (distribuiti tra gli artisti, inseriti da utenti casuali)
  - 130 Associazioni Album-Artista (alcuni album hanno più artisti)
  - 250 Copie fisiche (collezionate dagli utenti con formati e condizioni del progetto)

Include anche il download opzionale di copertine astratte per rendere
la visualizzazione nel catalogo esteticamente gradevole.

Esecuzione:
  python seed_large.py
"""

import sqlite3
import os
import random
import datetime
import urllib.request
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/scripts/
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATABASE_PATH = os.path.join(BACKEND_DIR, "instance", "groovebox.db")
COVERS_DIR = os.path.join(BACKEND_DIR, "uploads", "covers")

# Liste per la generazione di dati realistici
FIRST_NAMES = [
    "Luca", "Giulia", "Marco", "Sofia", "Francesco", "Alice", "Alessandro", "Emma", 
    "Andrea", "Giorgia", "Matteo", "Chiara", "Davide", "Martina", "Lorenzo", "Sara", 
    "Federico", "Elena", "Riccardo", "Gaia", "Gabriele", "Anna", "Tommaso", "Francesca"
]

SURNAMES = [
    "Rossi", "Ferrari", "Russo", "Bianchi", "Esposito", "Colombo", "Romano", "Ricci", 
    "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Giordano", 
    "Mancini", "Rizzo", "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro", "Caruso"
]

GENRES = ["Rock / Alternative", "Pop", "Hip-Hop / Rap", "Electronic / Dance", "Ambient / Experimental", "Metal / Hard Rock", "Jazz / Blues", "Soul / R&B / Funk", "Reggae / Dub", "Folk / Acoustic", "Classical", "Soundtrack / OST", "World / Altro"]

FORMATS = ["Vinile", "CD", "Cassetta"]
CONDITIONS = ["Nuovo", "Come nuovo", "Buono", "Discreto", "Rovinato"]

ARTIST_NAMES = [
    # Band & Artisti Reali Popolari
    "Pink Floyd", "Daft Punk", "The Beatles", "Led Zeppelin", "Queen", "David Bowie", 
    "Michael Jackson", "Nirvana", "Madonna", "Eminem", "Radiohead", "Taylor Swift", 
    "Depeche Mode", "Massive Attack", "The Rolling Stones", "AC/DC", "Bob Marley", 
    "Stevie Wonder", "Miles Davis", "John Coltrane", "Jimi Hendrix", "Coldplay", 
    "U2", "The Cure", "Metallica", "Iron Maiden", "Fleetwood Mac", "Gorillaz",
    # Artisti generati realistici
    "The Sound Wave", "Luna & The Stars", "Midnight Echo", "Electric Dreams", 
    "The Velvet Grooves", "Acoustic Horizon", "Beat Syndicate", "Neon Nights",
    "Jungle Beats", "Dusty Records", "Aura Project", "Sub-Zero", "Vocal Theory",
    "Liquid Jazz Trio", "Symphony of Noise", "The Bassline Collective", "Coastal Breeze",
    "Future Funk", "Static Sky", "The Analog Club", "Echo Location", "Retro Grade",
    "Urban Poet", "Silver Strings", "Harmonic Waves", "The Rhythm Section",
    "Solaris", "Quantum Beats", "Gravity Well", "Frequency Shift", "Vibe Tribe", "Modulation"
]

ALBUM_NOUNS = [
    "Road", "Sky", "Mind", "Moon", "Silence", "Darkness", "Dream", "Sun", "Heart", 
    "Time", "Shadow", "Ocean", "River", "Voice", "Soul", "World", "Machine", "Space", 
    "Night", "Light", "City", "Forest", "Rain", "Fire", "Gold", "Wind", "Wave"
]

ALBUM_ADJECTIVES = [
    "Abbey", "Dark Side", "Electric", "Velvet", "Golden", "Silent", "Infinite", 
    "Secret", "Lost", "Midnight", "Pacific", "Urban", "Vintage", "Parallel", 
    "Digital", "Analog", "Cosmic", "Classic", "Wild", "Plastic", "Atomic", "Neon"
]

NOTES_POOL = [
    "Prima stampa originale", "Edizione limitata in vinile colorato", "Firmato dall'artista",
    "Condizioni della copertina leggermente usurate", "Include inserto fotografico originale",
    "Ristampa audiophile 180g", "Edizione speciale per il Record Store Day", "Copia promozionale",
    "Nessuna nota", None, None, None # per renderle meno frequenti
]

def download_placeholder_covers():
    """Scarica 10 immagini astratte da usare come copertine degli album."""
    os.makedirs(COVERS_DIR, exist_ok=True)
    print("-> Download di copertine di esempio in corso...")
    
    saved_files = []
    # Usiamo URL fissi da Picsum Photos per avere immagini stabili
    urls = [
        ("https://picsum.photos/id/10/300/300", "cover_1.jpg"),
        ("https://picsum.photos/id/20/300/300", "cover_2.jpg"),
        ("https://picsum.photos/id/29/300/300", "cover_3.jpg"),
        ("https://picsum.photos/id/36/300/300", "cover_4.jpg"),
        ("https://picsum.photos/id/48/300/300", "cover_5.jpg"),
        ("https://picsum.photos/id/60/300/300", "cover_6.jpg"),
        ("https://picsum.photos/id/76/300/300", "cover_7.jpg"),
        ("https://picsum.photos/id/80/300/300", "cover_8.jpg"),
        ("https://picsum.photos/id/104/300/300", "cover_9.jpg"),
        ("https://picsum.photos/id/111/300/300", "cover_10.jpg"),
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url, filename in urls:
        path = os.path.join(COVERS_DIR, filename)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response, open(path, "wb") as out_file:
                out_file.write(response.read())
            saved_files.append(filename)
        except Exception as e:
            print(f"   [!] Impossibile scaricare {filename}: {e} (saltato)")
            
    print(f"-> Scaricate con successo {len(saved_files)} copertine.")
    return saved_files

def main():
    if not os.path.exists(DATABASE_PATH):
        print(f"[!] Errore: File database '{DATABASE_PATH}' non trovato. Esegui prima 'database.py'.")
        return

    print("====================================================")
    print("GrooveBox - Popolamento Database (Large Seed)")
    print("====================================================")
    
    # 1. Scarica le copertine
    cover_files = download_placeholder_covers()
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    try:
        # Pulisci i dati esistenti tranne l'utente admin (id_user=1) e mario_rossi (id_user=2)
        print("-> Pulizia delle tabelle (esclusi utenti di default)...")
        cursor.execute("DELETE FROM PHYSICAL_COPY")
        cursor.execute("DELETE FROM ALBUM_ARTIST")
        cursor.execute("DELETE FROM ALBUM")
        cursor.execute("DELETE FROM ARTIST")
        cursor.execute("DELETE FROM USER WHERE id_user > 2")
        conn.commit()
        
        # 2. Genera 50 Utenti Collector (id da 3 a 52)
        print("-> Generazione di 50 Collector...")
        password_hash = generate_password_hash("password123") # password comune per testare facilmente
        user_ids = []
        
        # Aggiungiamo mario_rossi (id_user = 2) ai nostri ID attivi
        user_ids.append(2)
        
        used_usernames = {"admin", "mario_rossi"}
        while len(user_ids) < 51:  # 50 nuovi collector + mario_rossi
            name = random.choice(FIRST_NAMES)
            surname = random.choice(SURNAMES)
            username = f"{name.lower()}.{surname.lower()}"
            
            # Evita duplicati di username
            if username in used_usernames:
                username = f"{username}{random.randint(10, 99)}"
            
            used_usernames.add(username)
            email = f"{username}@email.com"
            
            cursor.execute(
                """INSERT INTO USER (username, name, surname, email, passwordHash, role)
                   VALUES (?, ?, ?, ?, ?, 'collector')""",
                (username, name, surname, email, password_hash)
            )
            user_ids.append(cursor.lastrowid)
            
        print(f"   [OK] Creati {len(user_ids) - 1} nuovi collector.")

        # 3. Genera 60 Artisti
        print("-> Generazione di 60 Artisti...")
        artist_ids = []
        
        # Prendi i primi 60 nomi dalla lista (se ce ne sono abbastanza, altrimenti genera proceduralmente)
        artists_to_insert = ARTIST_NAMES[:60]
        while len(artists_to_insert) < 60:
            new_art = f"{random.choice(FIRST_NAMES)} {random.choice(SURNAMES)} Project"
            if new_art not in artists_to_insert:
                artists_to_insert.append(new_art)
                
        for name in artists_to_insert:
            cursor.execute("INSERT INTO ARTIST (name) VALUES (?)", (name,))
            artist_ids.append(cursor.lastrowid)
            
        print(f"   [OK] Creati {len(artist_ids)} artisti.")

        # 4. Genera 120 Album
        print("-> Generazione di 120 Album...")
        album_ids = []
        used_titles = set()
        
        for i in range(120):
            # Crea un titolo realistico
            title = f"{random.choice(ALBUM_ADJECTIVES)} {random.choice(ALBUM_NOUNS)}"
            if title in used_titles:
                title = f"{title} Vol. {random.randint(2, 4)}"
            used_titles.add(title)
            
            year = random.randint(1965, 2026)
            genre = random.choice(GENRES)
            
            # Assegna una copertina a caso tra quelle scaricate (opzionale)
            cover = random.choice(cover_files) if cover_files and random.random() > 0.3 else None
            
            # Inserito da un utente casuale
            creator_id = random.choice(user_ids)
            
            cursor.execute(
                """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user)
                   VALUES (?, ?, ?, ?, ?)""",
                (title, year, genre, cover, creator_id)
            )
            album_ids.append(cursor.lastrowid)
            
        print(f"   [OK] Creati {len(album_ids)} album.")

        # 5. Genera 130 Associazioni Album-Artista (N:M)
        print("-> Generazione di 130 Associazioni Album-Artista...")
        associations = set()
        
        # Assicura che ogni album abbia almeno un artista
        for album_id in album_ids:
            artist_id = random.choice(artist_ids)
            cursor.execute(
                "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                (album_id, artist_id)
            )
            associations.add((album_id, artist_id))
            
        # Aggiungi associazioni extra fino a raggiungere 130 (album con artisti multipli/collaborazioni)
        while len(associations) < 130:
            album_id = random.choice(album_ids)
            artist_id = random.choice(artist_ids)
            
            if (album_id, artist_id) not in associations:
                cursor.execute(
                    "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                    (album_id, artist_id)
                )
                associations.add((album_id, artist_id))
                
        print(f"   [OK] Create {len(associations)} relazioni album-artista.")

        # 6. Genera 250 Copie Fisiche
        print("-> Generazione di 250 Copie Fisiche per le collezioni private...")
        today = datetime.date.today()
        
        for _ in range(250):
            album_id = random.choice(album_ids)
            user_id = random.choice(user_ids)
            fmt = random.choice(FORMATS)
            cond = random.choice(CONDITIONS)
            
            # Data di aggiunta casuale negli ultimi 365 giorni
            days_ago = random.randint(0, 365)
            added_date = (today - datetime.timedelta(days=days_ago)).isoformat()
            
            notes = random.choice(NOTES_POOL)
            
            cursor.execute(
                """INSERT INTO PHYSICAL_COPY (format, condition, addedDate, personalNotes, id_user, id_album)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (fmt, cond, added_date, notes, user_id, album_id)
            )
            
        print("   [OK] Create 250 copie fisiche.")
        
        conn.commit()
        print("\n====================================================")
        print("POPOLAMENTO COMPLETATO CON SUCCESSO!")
        print("====================================================")
        print(f"- Utenti totali: {len(user_ids)} (tutti con password: 'password123')")
        print(f"- Artisti: {len(artist_ids)}")
        print(f"- Album nel catalogo globale: {len(album_ids)}")
        print(f"- Copie fisiche totali distribuite nelle librerie: 250")
        print("====================================================")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[!] ERRORE DURANTE IL SEEDING: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
