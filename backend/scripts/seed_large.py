"""
GrooveBox - Script di Popolamento Database Large (Seeding)
===========================================================
Crea:
  - 50 Collector (Utenti)
  - Catalogo di Album Reali (via iTunes API) completi di copertine ad alta risoluzione
  - Artisti Reali e relative Associazioni Album-Artista
  - 250 Copie fisiche (collezionate dagli utenti con formati e condizioni del progetto)

Esecuzione:
  python seed_large.py
"""

import sqlite3
import os
import random
import datetime
import urllib.request
import urllib.parse
import json
import re
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/scripts/
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATABASE_PATH = os.path.join(BACKEND_DIR, "instance", "groovebox.db")
COVERS_DIR = os.path.join(BACKEND_DIR, "uploads", "covers")

# Liste per la generazione di dati realistici per utenti e logiche di business
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
# Allineato ai vincoli CHECK del database.py ('Nuovo', 'Come nuovo', 'Buono', 'Discreto', 'Rovinato')
CONDITIONS = ["Nuovo", "Come nuovo", "Buono", "Discreto", "Rovinato"]

NOTES_POOL = [
    "Prima stampa originale", "Edizione limitata in vinile colorato", "Firmato dall'artista",
    "Condizioni della copertina leggermente usurate", "Include inserto fotografico originale",
    "Ristampa audiophile 180g", "Edizione speciale per il Record Store Day", "Copia promozionale",
    "Nessuna nota", None, None, None # per renderle meno frequenti
]

# Pool di artisti italiani e internazionali da usare per raggiungere la quota di 60 artisti totali
EXTRA_ARTISTS_POOL = [
    "Fabrizio De André", "Francesco Guccini", "Lucio Battisti", "Lucio Dalla",
    "Vasco Rossi", "Ligabue", "Jovanotti", "Subsonica", "Verdena", "Afterhours",
    "Mina", "Adriano Celentano", "Claudio Baglioni", "Gianna Nannini", "Franco Battiato",
    "Caparezza", "Fabri Fibra", "Marracash", "Guè", "Salmo", "Sfera Ebbasta", "Madame",
    "Rino Gaetano", "Francesco De Gregori", "Antonello Venditti", "Pino Daniele", "Zen Circus",
    "Brunori Sas", "Calibro 35", "Baustelle", "Lo Stato Sociale", "Maneskin", "Ghemon"
]

def split_artist_names(artist_string):
    """
    Splitta i nomi degli artisti separandoli quando contengono congiunzioni o parole chiave 
    di collaborazione ('&', 'and', 'feat.', 'featuring'), restituendo una lista di nomi puliti.
    """
    if not artist_string:
        return []
    # Sostituisce i delimitatori comuni con una barra verticale '|'
    temp = re.sub(r'\s+&\s+|\s+and\s+|\s+feat\.\s+|\s+featuring\s+', '|', artist_string, flags=re.IGNORECASE)
    # Splitta per barra e rimuove spazi extra
    return [name.strip() for name in temp.split('|') if name.strip()]

def fetch_real_albums_and_covers(target_count=120):
    """
    Usa l'API pubblica di iTunes per recuperare album reali e scaricare le copertine.
    Restituisce una lista di dizionari con i dati pronti per il DB.
    """
    os.makedirs(COVERS_DIR, exist_ok=True)
    print("-> Interrogazione API iTunes per recuperare album reali in corso...")
    
    search_artists = [
        "Pink Floyd", "Daft Punk", "Nirvana", "The Beatles", "Miles Davis", 
        "Kendrick Lamar", "Taylor Swift", "Metallica", "Bob Marley", "Radiohead",
        "Michael Jackson", "Queen", "David Bowie", "The Cure", "Fleetwood Mac",
        "Eminem", "Coldplay", "Gorillaz", "The Rolling Stones", "Led Zeppelin"
    ]
    
    real_albums = []
    headers = {"User-Agent": "GrooveBoxUniversityProject/1.0"}
    
    for artist in search_artists:
        if len(real_albums) >= target_count:
            break
            
        query = urllib.parse.quote(artist)
        url = f"https://itunes.apple.com/search?term={query}&entity=album&limit=10"
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read())
                
                for item in data.get('results', []):
                    title = item.get('collectionName')
                    artist_name = item.get('artistName')
                    release_year = item.get('releaseDate', '2020')[:4]
                    
                    genre = random.choice(GENRES) 
                    
                    # Copertina in alta risoluzione
                    artwork_url = item.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
                    
                    if not title or not artwork_url:
                        continue
                        
                    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title)[:30]
                    filename = f"{safe_title}_{random.randint(1000, 9999)}.jpg"
                    filepath = os.path.join(COVERS_DIR, filename)
                    
                    # Evita di riscaricare la stessa immagine se si riavvia lo script
                    if not os.path.exists(filepath):
                        img_req = urllib.request.Request(artwork_url, headers=headers)
                        with urllib.request.urlopen(img_req, timeout=5) as img_response, open(filepath, "wb") as out_file:
                            out_file.write(img_response.read())
                    
                    real_albums.append({
                        "title": title,
                        "artist": artist_name,
                        "year": int(release_year),
                        "genre": genre,
                        "cover": filename
                    })
                    
                    print(f"   [+] Elaborato: {title} - {artist_name}")
                    
                    if len(real_albums) >= target_count:
                        break
                        
        except Exception as e:
            print(f"   [!] Errore fetch artista {artist}: {e}")
            
    print(f"-> Recuperati {len(real_albums)} album reali completi di copertina.")
    return real_albums

def main():
    if not os.path.exists(DATABASE_PATH):
        print(f"[!] Errore: File database '{DATABASE_PATH}' non trovato. Esegui prima la creazione del DB.")
        return

    print("====================================================")
    print("GrooveBox - Popolamento Database (Real Data Seed)")
    print("====================================================")
    
    # 1. Recupera album reali e scarica le copertine
    real_albums_data = fetch_real_albums_and_covers(target_count=120)
    
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
        
        # 2. Genera Collector in modo che il totale nel DB sia ESATTAMENTE 50 (compresi admin e mario_rossi)
        print("-> Generazione di Collector (totale target utenti: 50)...")
        password_hash = generate_password_hash("password123") 
        user_ids = [1, 2] # Utenti di default esistenti nel DB
        
        used_usernames = {"admin", "mario_rossi"}
        while len(user_ids) < 50: 
            name = random.choice(FIRST_NAMES)
            surname = random.choice(SURNAMES)
            username = f"{name.lower()}.{surname.lower()}"
            
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
            
        print(f"   [OK] Creati {len(user_ids) - 2} nuovi collector (Totale utenti nel DB: 50).")

        # 3. Estrai e splitta gli Artisti per gestire le collaborazioni separatamente
        print("-> Registrazione Artisti nel DB (suddividendo le collaborazioni)...")
        artist_id_map = {}
        for album_data in real_albums_data:
            # Splitta il nome dell'artista
            names = split_artist_names(album_data["artist"])
            for name in names:
                if name not in artist_id_map:
                    cursor.execute("INSERT INTO ARTIST (name) VALUES (?)", (name,))
                    artist_id_map[name] = cursor.lastrowid
        
        # Assicurati che ci siano esattamente 60 artisti nel DB (riempi con EXTRA_ARTISTS_POOL se necessario)
        all_artist_ids = list(artist_id_map.values())
        extra_artists = list(set(EXTRA_ARTISTS_POOL) - set(artist_id_map.keys()))
        random.shuffle(extra_artists)
        
        while len(all_artist_ids) < 60:
            if extra_artists:
                extra_name = extra_artists.pop()
            else:
                extra_name = f"Artista di Supporto {len(all_artist_ids) + 1}"
            cursor.execute("INSERT INTO ARTIST (name) VALUES (?)", (extra_name,))
            artist_id = cursor.lastrowid
            all_artist_ids.append(artist_id)
            artist_id_map[extra_name] = artist_id

        # Se per qualche motivo superiamo 60 (es. iTunes restituisce troppe collab), limitiamo a 60
        if len(all_artist_ids) > 60:
            # Per mantenere l'integrità, rimuoviamo quelli di troppo dal DB (non usati)
            artists_to_remove = all_artist_ids[60:]
            all_artist_ids = all_artist_ids[:60]
            for aid in artists_to_remove:
                cursor.execute("DELETE FROM ARTIST WHERE id_artist = ?", (aid,))
                # Rimuovi anche dalla mappa
                for k, v in list(artist_id_map.items()):
                    if v == aid:
                        del artist_id_map[k]

        print(f"   [OK] Inseriti {len(all_artist_ids)} Artisti unici nel DB (target esatto: 60).")

        # 4. Genera esattamente 120 Album ed associa le relazioni
        print("-> Inserimento di 120 Album ed associazione delle relazioni Album-Artista...")
        album_ids = []
        album_artist_relations = []
        
        for album_data in real_albums_data:
            creator_id = random.choice(user_ids)
            cursor.execute(
                """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user)
                   VALUES (?, ?, ?, ?, ?)""",
                (album_data["title"], album_data["year"], album_data["genre"], album_data["cover"], creator_id)
            )
            album_id = cursor.lastrowid
            album_ids.append(album_id)
            
            # Recupera tutti gli artisti splittati associati a questo album
            names = split_artist_names(album_data["artist"])
            # Colleghiamo solo gli artisti che fanno parte dei nostri 60 inseriti
            associated_artist_ids = [artist_id_map[name] for name in names if name in artist_id_map]
            
            # Se per qualche motivo l'artista non è nel DB (es. rimosso per limite 60), usa un fallback
            if not associated_artist_ids:
                associated_artist_ids = [random.choice(all_artist_ids)]
                
            for artist_id in associated_artist_ids:
                cursor.execute(
                    "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                    (album_id, artist_id)
                )
                album_artist_relations.append((album_id, artist_id))
            
        # Adesso sistemiamo le relazioni in ALBUM_ARTIST per arrivare a ESATTAMENTE 130
        current_relations_count = len(album_artist_relations)
        
        if current_relations_count < 130:
            # Aggiungiamo collaborazioni a caso per raggiungere quota 130
            needed = 130 - current_relations_count
            print(f"   [i] Relazioni attuali: {current_relations_count}. Aggiunta di {needed} collaborazioni per raggiungere 130...")
            
            # Evitiamo duplicati prendendo album che non hanno già tutte le relazioni
            candidate_albums = list(album_ids)
            random.shuffle(candidate_albums)
            
            for album_id in candidate_albums:
                if needed <= 0:
                    break
                # Artisti già associati a questo album
                existing_aids = [r[1] for r in album_artist_relations if r[0] == album_id]
                # Scegli un artista che non sia già associato
                available_aids = [aid for aid in all_artist_ids if aid not in existing_aids]
                if available_aids:
                    sec_artist_id = random.choice(available_aids)
                    cursor.execute(
                        "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                        (album_id, sec_artist_id)
                    )
                    album_artist_relations.append((album_id, sec_artist_id))
                    needed -= 1
                    
        elif current_relations_count > 130:
            # Rimuoviamo relazioni di troppo (mantenendone sempre almeno 1 per album)
            excess = current_relations_count - 130
            print(f"   [i] Relazioni attuali: {current_relations_count}. Rimozione di {excess} relazioni extra per rientrare nel target di 130...")
            
            # Trova relazioni che possono essere rimosse (l'album deve avere più di 1 artista)
            album_counts = {}
            for album_id, _ in album_artist_relations:
                album_counts[album_id] = album_counts.get(album_id, 0) + 1
                
            for rel in list(album_artist_relations):
                if excess <= 0:
                    break
                album_id, artist_id = rel
                if album_counts[album_id] > 1:
                    cursor.execute(
                        "DELETE FROM ALBUM_ARTIST WHERE id_album = ? AND id_artist = ?",
                        (album_id, artist_id)
                    )
                    album_artist_relations.remove(rel)
                    album_counts[album_id] -= 1
                    excess -= 1

        print(f"   [OK] Inseriti {len(album_ids)} Album nel DB.")
        print(f"   [OK] Create {len(album_artist_relations)} relazioni in ALBUM_ARTIST (target esatto: 130).")

        # 5. Genera esattamente 250 Copie Fisiche
        print("-> Generazione di 250 Copie Fisiche per le collezioni private...")
        today = datetime.date.today()
        
        for _ in range(250):
            album_id = random.choice(album_ids)
            user_id = random.choice(user_ids)
            fmt = random.choice(FORMATS)
            cond = random.choice(CONDITIONS)
            
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
        print(f"- Utenti totali nel DB: {len(user_ids)} (target: 50)")
        print(f"- Artisti totali nel DB: {len(all_artist_ids)} (target: 60)")
        print(f"- Album inseriti a catalogo: {len(album_ids)} (target: 120)")
        print(f"- Relazioni Album-Artista inserite: {len(album_artist_relations)} (target: 130)")
        print(f"- Copie fisiche totali distribuite: 250 (target: 250)")
        print("====================================================")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[!] ERRORE DURANTE IL SEEDING: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
