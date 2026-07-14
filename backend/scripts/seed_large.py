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
import json
import re
import time
import requests
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/scripts/
BACKEND_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(BACKEND_DIR, ".env"))
DATABASE_PATH = os.path.join(BACKEND_DIR, "instance", "groovebox.db")
COVERS_DIR = os.path.join(BACKEND_DIR, "uploads", "covers")
ARTISTS_DIR = os.path.join(BACKEND_DIR, "uploads", "artists")

# Liste per la generazione di dati realistici per utenti e logiche di business
FIRST_NAMES = ["Luca", "Giulia", "Marco", "Sofia", "Andrea"]
SURNAMES = ["Rossi", "Ferrari", "Bianchi", "Russo", "Conti"]



FORMATS = ["Vinile", "CD", "Cassetta"]
# Allineato ai vincoli CHECK del database.py ('Nuovo', 'Come nuovo', 'Buono', 'Discreto', 'Rovinato')
CONDITIONS = ["Nuovo", "Come nuovo", "Buono", "Discreto", "Rovinato"]

NOTES_POOL = [
    "Prima stampa originale", "Edizione limitata in vinile colorato", "Firmato dall'artista",
    "Condizioni della copertina leggermente usurate", "Include inserto fotografico originale",
    "Ristampa audiophile 180g", "Edizione speciale per il Record Store Day", "Copia promozionale",
    "Nessuna nota", None, None, None # per renderle meno frequenti
]

# Pool di artisti reali da usare per raggiungere la quota di 60 artisti totali
EXTRA_ARTISTS_POOL = ["Lucio Dalla", "Mina", "Franco Battiato", "Pino Daniele", "Lucio Battisti"]

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



def clean_artist_name(name):
    if not name:
        return ""
    return re.sub(r'\s*\(\d+\)$', '', name).strip()

def clean_title(title):
    if not title:
        return ""
    if " = " in title:
        parts = [p.strip() for p in title.split(" = ")]
        if len(parts) >= 2:
            non_latin_pattern = re.compile(r'[\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff\u0400-\u04ff\u1100-\u11ff\uac00-\ud7af]')
            has_non_latin_0 = bool(non_latin_pattern.search(parts[0]))
            has_non_latin_1 = bool(non_latin_pattern.search(parts[1]))
            
            if has_non_latin_0 and not has_non_latin_1:
                return parts[1]
            if has_non_latin_1 and not has_non_latin_0:
                return parts[0]
            return parts[0]
    return title.strip()

def map_genre(genres, styles):
    terms = []
    if genres:
        terms.append(genres[0])
    if styles:
        terms.extend(styles[:2])
    unique_terms = []
    for t in terms:
        if t not in unique_terms:
            unique_terms.append(t)
    return ", ".join(unique_terms[:2]) if unique_terms else "Unknown"

def fetch_real_albums_and_covers(target_count=120):
    """
    Usa l'API di Discogs per recuperare album reali e scaricare le copertine.
    Estrae anche tracklist, casa discografica, numero di catalogo, codice a barre e paese di stampa.
    """
    os.makedirs(COVERS_DIR, exist_ok=True)
    print("-> Interrogazione API Discogs per recuperare album reali in corso...")
    
    key = os.environ.get("DISCOGS_CONSUMER_KEY")
    secret = os.environ.get("DISCOGS_CONSUMER_SECRET")
    if not key or not secret:
        print("[!] Errore: DISCOGS_CONSUMER_KEY o DISCOGS_CONSUMER_SECRET non impostate nel file .env!")
        return []
        
    headers = {
        "User-Agent": "GrooveBoxSeed/1.0",
        "Authorization": f"Discogs key={key.strip()}, secret={secret.strip()}"
    }
    
    search_artists = [
        "Tyler, the Creator", "Daft Punk", "Pino Daniele", "The Cure", "Lucio Dalla"
    ]
    
    real_albums = []
    
    for artist in search_artists:
        if len(real_albums) >= target_count:
            break
            
        print(f"-> Ricerca release per {artist} su Discogs...")
        search_url = "https://api.discogs.com/database/search"
        params = {
            "artist": artist,
            "type": "release",
            "per_page": 15
        }
        
        try:
            res = requests.get(search_url, headers=headers, params=params, timeout=5)
            if res.status_code == 429:
                print("   [!] Raggiunto rate limit Discogs, attesa di 10 secondi...")
                time.sleep(10)
                res = requests.get(search_url, headers=headers, params=params, timeout=5)
                
            res.raise_for_status()
            results = res.json().get("results", [])
            
            for item in results:
                if len(real_albums) >= target_count:
                    break
                    
                release_id = item.get("id")
                if not release_id:
                    continue
                    
                detail_url = f"https://api.discogs.com/releases/{release_id}"
                time.sleep(1.1)  # Garantisce il rispetto dei limiti di rate limit (max 60 req/min)
                
                try:
                    detail_res = requests.get(detail_url, headers=headers, timeout=5)
                    if detail_res.status_code == 429:
                        print("   [!] Raggiunto rate limit Discogs nei dettagli, attesa di 15 secondi...")
                        time.sleep(15)
                        detail_res = requests.get(detail_url, headers=headers, timeout=5)
                        
                    detail_res.raise_for_status()
                    data = detail_res.json()
                    
                    title = clean_title(data.get("title"))
                    artists_data = data.get("artists", [])
                    if not title or not artists_data:
                        continue
                        
                    discogs_artist_name = clean_artist_name(artists_data[0].get("name", ""))
                    
                    if artist.lower() not in discogs_artist_name.lower():
                        continue
                        
                    if any(a["title"].lower() == title.lower() for a in real_albums):
                        continue
                        
                    year = data.get("year")
                    if not year and data.get("released"):
                        released_str = data.get("released", "")
                        if len(released_str) >= 4 and released_str[:4].isdigit():
                            year = int(released_str[:4])
                    if not year:
                        year = 2020
                        
                    genre = map_genre(data.get("genres", []), data.get("styles", []))
                    
                    tracklist = []
                    for track in data.get("tracklist", []):
                        if track.get("type_", "track") == "track":
                            tracklist.append({
                                "position": track.get("position", ""),
                                "title": track.get("title", ""),
                                "duration": track.get("duration", "")
                            })
                            
                    if len(tracklist) < 4:
                        continue
                        
                    label_name = None
                    catno = None
                    labels = data.get("labels", [])
                    if labels:
                        label_name = clean_artist_name(labels[0].get("name", ""))
                        catno = labels[0].get("catno")
                        
                    barcode = None
                    for ident in data.get("identifiers", []):
                        if ident.get("type") == "Barcode":
                            barcode = ident.get("value", "").strip().replace(" ", "")
                            break
                            
                    country = data.get("country")
                    
                    cover_url = None
                    images = data.get("images", [])
                    if images:
                        primary_images = [img for img in images if img.get("type") == "primary"]
                        if primary_images:
                            cover_url = primary_images[0].get("uri")
                        else:
                            cover_url = images[0].get("uri")
                    if not cover_url:
                        cover_url = data.get("thumb")
                        
                    cover_filename = None
                    if cover_url:
                        ext = "jpg"
                        if ".png" in cover_url.lower():
                            ext = "png"
                        elif ".webp" in cover_url.lower():
                            ext = "webp"
                        
                        cover_filename = f"album_discogs_{release_id}.{ext}"
                        filepath = os.path.join(COVERS_DIR, cover_filename)
                        
                        if not os.path.exists(filepath):
                            img_res = requests.get(cover_url, headers=headers, timeout=5)
                            if img_res.status_code == 200:
                                with open(filepath, "wb") as f:
                                    f.write(img_res.content)
                            else:
                                cover_filename = None
                                
                    real_albums.append({
                        "title": title,
                        "artist": discogs_artist_name,
                        "artists": [{"name": clean_artist_name(a.get("name")), "discogs_id": a.get("id")} for a in artists_data],
                        "year": year,
                        "genre": genre,
                        "cover": cover_filename,
                        "discogs_id": release_id,
                        "tracklist": tracklist,
                        "label": label_name,
                        "catno": catno,
                        "barcode": barcode,
                        "country": country
                    })
                    print(f"   [+] Elaborato: {title} - {discogs_artist_name} ({genre})")
                    
                    if len(real_albums) >= target_count:
                        break
                        
                except Exception as ex:
                    print(f"   [!] Errore nel caricamento del dettaglio release {release_id}: {ex}")
                    
        except Exception as e:
            print(f"   [!] Errore nella ricerca per {artist}: {e}")
            
    print(f"-> Recuperati {len(real_albums)} album reali da Discogs.")
    return real_albums
def main():
    if not os.path.exists(DATABASE_PATH):
        print(f"[!] Errore: File database '{DATABASE_PATH}' non trovato. Esegui prima la creazione del DB.")
        return

    print("====================================================")
    print("GrooveBox - Popolamento Database (Real Data Seed)")
    print("====================================================")
    
    # 1. Recupera album reali e scarica le copertine (ridotto a 20 per velocità di debugging)
    real_albums_data = fetch_real_albums_and_covers(target_count=20)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    try:
        # Pulisci i dati esistenti tranne l'utente admin (id_user=1) e test (id_user=2)
        print("-> Pulizia delle tabelle (esclusi utenti di default)...")
        cursor.execute("DELETE FROM PHYSICAL_COPY")
        cursor.execute("DELETE FROM ALBUM_ARTIST")
        cursor.execute("DELETE FROM ALBUM")
        cursor.execute("DELETE FROM ARTIST")
        cursor.execute("DELETE FROM USER WHERE id_user > 2")
        conn.commit()
        
        # 2. Genera Collector in modo che il totale nel DB sia ESATTAMENTE 5 (compresi admin e test)
        print("-> Generazione di Collector (totale target utenti: 5)...")
        password_hash = generate_password_hash("password123") 
        user_ids = [1, 2] # Utenti di default esistenti nel DB
        
        used_usernames = {"admin", "test"}
        while len(user_ids) < 5: 
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
            
        print(f"   [OK] Creati {len(user_ids) - 2} nuovi collector (Totale utenti nel DB: 5).")

        # 3. Estrai e splitta gli Artisti per gestire le collaborazioni separatamente, arricchendoli da Discogs
        print("-> Registrazione Artisti nel DB (recuperando biografia e foto da Discogs)...")
        os.makedirs(ARTISTS_DIR, exist_ok=True)
        artist_id_map = {}
        
        # Definisci gli header per le chiamate Discogs
        key = os.environ.get("DISCOGS_CONSUMER_KEY")
        secret = os.environ.get("DISCOGS_CONSUMER_SECRET")
        headers = {}
        if key and secret:
            headers = {
                "User-Agent": "GrooveBoxSeed/1.0",
                "Authorization": f"Discogs key={key.strip()}, secret={secret.strip()}"
            }
        
        # Mappa i nomi degli artisti ai loro discogs_id
        artist_discogs_map = {}
        for album_data in real_albums_data:
            for art in album_data.get("artists", []):
                artist_discogs_map[art["name"]] = art["discogs_id"]
                
        for album_data in real_albums_data:
            names = split_artist_names(album_data["artist"])
            for name in names:
                if name not in artist_id_map:
                    discogs_id = artist_discogs_map.get(name)
                    bio = ""
                    photo_filename = None
                    
                    if discogs_id and headers:
                        print(f"   -> Recupero dettagli artista {name} (ID: {discogs_id})...")
                        time.sleep(1.1)  # Rispetta il rate limit
                        try:
                            art_url = f"https://api.discogs.com/artists/{discogs_id}"
                            art_res = requests.get(art_url, headers=headers, timeout=5)
                            if art_res.status_code == 429:
                                print("      [!] Rate limit raggiunto per artista, attesa di 15 secondi...")
                                time.sleep(15)
                                art_res = requests.get(art_url, headers=headers, timeout=5)
                                
                            art_res.raise_for_status()
                            art_data = art_res.json()
                            bio = art_data.get("profile", "")
                            
                            # Estrai foto
                            photo_url = None
                            images = art_data.get("images", [])
                            if images:
                                prim = [img for img in images if img.get("type") == "primary"]
                                photo_url = prim[0].get("uri") if prim else images[0].get("uri")
                                
                            if photo_url:
                                photo_filename = f"artist_discogs_{discogs_id}.jpg"
                                filepath = os.path.join(ARTISTS_DIR, photo_filename)
                                if not os.path.exists(filepath):
                                    img_res = requests.get(photo_url, headers=headers, timeout=5)
                                    if img_res.status_code == 200:
                                        with open(filepath, "wb") as f:
                                            f.write(img_res.content)
                                    else:
                                        photo_filename = None
                        except Exception as e:
                            print(f"      [!] Errore nel recupero dell'artista {name}: {e}")
                            
                    cursor.execute(
                        "INSERT INTO ARTIST (name, discogs_id, biography, image_path) VALUES (?, ?, ?, ?)",
                        (name, discogs_id, bio, photo_filename)
                    )
                    artist_id_map[name] = cursor.lastrowid
        
        # Assicurati che ci siano esattamente 10 artisti nel DB (riempi con EXTRA_ARTISTS_POOL se necessario)
        all_artist_ids = list(artist_id_map.values())
        extra_artists = list(set(EXTRA_ARTISTS_POOL) - set(artist_id_map.keys()))
        random.shuffle(extra_artists)
        
        while len(all_artist_ids) < 10:
            if extra_artists:
                extra_name = extra_artists.pop()
            else:
                extra_name = f"Artista di Supporto {len(all_artist_ids) + 1}"
            cursor.execute("INSERT INTO ARTIST (name) VALUES (?)", (extra_name,))
            artist_id = cursor.lastrowid
            all_artist_ids.append(artist_id)
            artist_id_map[extra_name] = artist_id
 
        # Se per qualche motivo superiamo 10, limitiamo a 10
        if len(all_artist_ids) > 10:
            artists_to_remove = all_artist_ids[10:]
            all_artist_ids = all_artist_ids[:10]
            for aid in artists_to_remove:
                cursor.execute("DELETE FROM ARTIST WHERE id_artist = ?", (aid,))
                for k, v in list(artist_id_map.items()):
                    if v == aid:
                        del artist_id_map[k]
 
        print(f"   [OK] Inseriti {len(all_artist_ids)} Artisti unici nel DB (target esatto: 10).")

        # 4. Genera esattamente 20 Album ed associa le relazioni
        print("-> Inserimento di 20 Album ed associazione delle relazioni Album-Artista...")
        album_ids = []
        album_artist_relations = []
        
        for album_data in real_albums_data:
            creator_id = random.choice(user_ids)
            cursor.execute(
                """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user, discogs_id, tracklist, label, catno, barcode, country)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    album_data["title"], 
                    album_data["year"], 
                    album_data["genre"], 
                    album_data["cover"], 
                    creator_id,
                    album_data.get("discogs_id"),
                    json.dumps(album_data.get("tracklist")) if album_data.get("tracklist") else None,
                    album_data.get("label"),
                    album_data.get("catno"),
                    album_data.get("barcode"),
                    album_data.get("country")
                )
            )
            album_id = cursor.lastrowid
            album_ids.append(album_id)
            
            # Recupera tutti gli artisti splittati associati a questo album
            names = split_artist_names(album_data["artist"])
            associated_artist_ids = [artist_id_map[name] for name in names if name in artist_id_map]
            
            if not associated_artist_ids:
                associated_artist_ids = [random.choice(all_artist_ids)]
                
            for artist_id in associated_artist_ids:
                cursor.execute(
                    "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                    (album_id, artist_id)
                )
                album_artist_relations.append((album_id, artist_id))
            
        # Sistemiamo le relazioni in ALBUM_ARTIST per arrivare a ESATTAMENTE 22
        current_relations_count = len(album_artist_relations)
        
        if current_relations_count < 22:
            needed = 22 - current_relations_count
            print(f"   [i] Relazioni attuali: {current_relations_count}. Aggiunta di {needed} collaborazioni per raggiungere 22...")
            
            candidate_albums = list(album_ids)
            random.shuffle(candidate_albums)
            
            for album_id in candidate_albums:
                if needed <= 0:
                    break
                existing_aids = [r[1] for r in album_artist_relations if r[0] == album_id]
                available_aids = [aid for aid in all_artist_ids if aid not in existing_aids]
                if available_aids:
                    sec_artist_id = random.choice(available_aids)
                    cursor.execute(
                        "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                        (album_id, sec_artist_id)
                    )
                    album_artist_relations.append((album_id, sec_artist_id))
                    needed -= 1
                    
        elif current_relations_count > 22:
            excess = current_relations_count - 22
            print(f"   [i] Relazioni attuali: {current_relations_count}. Rimozione di {excess} relazioni extra per rientrare nel target di 22...")
            
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
        print(f"   [OK] Create {len(album_artist_relations)} relazioni in ALBUM_ARTIST (target esatto: 22).")

        # 5. Genera esattamente 30 Copie Fisiche
        print("-> Generazione di 30 Copie Fisiche per le collezioni private...")
        today = datetime.date.today()
        
        for _ in range(30):
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
            
        print("   [OK] Create 30 copie fisiche.")
        
        conn.commit()
        print("\n====================================================")
        print("POPOLAMENTO COMPLETATO CON SUCCESSO!")
        print("====================================================")
        print(f"- Utenti totali nel DB: {len(user_ids)} (target: 5)")
        print(f"- Artisti totali nel DB: {len(all_artist_ids)} (target: 10)")
        print(f"- Album inseriti a catalogo: {len(album_ids)} (target: 20)")
        print(f"- Relazioni Album-Artista inserite: {len(album_artist_relations)} (target: 22)")
        print(f"- Copie fisiche totali distribuite: 30 (target: 30)")
        print("====================================================")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[!] ERRORE DURANTE IL SEEDING: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
