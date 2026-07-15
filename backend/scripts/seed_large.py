import os
import random
import datetime
import json
import re
import time
import requests
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/scripts/
BACKEND_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(BACKEND_DIR, ".env"))
DATABASE_PATH = os.path.join(BACKEND_DIR, "instance", "groovebox.db")
COVERS_DIR = os.path.join(BACKEND_DIR, "uploads", "covers")
ARTISTS_DIR = os.path.join(BACKEND_DIR, "uploads", "artists")

# ====================================================
# CONFIGURAZIONE DEL SEED (Modificabile al volo)
# ====================================================
NUM_COLLECTORS = 3       # Numero di utenti collezionisti fittizi da creare (oltre ad admin e test)
NUM_COPIES = 10          # Numero totale di copie fisiche da distribuire tra le collezioni

# ID reali di release Discogs da importare per il seeding
# 1. Daft Punk - Discovery (169648)
# 2. Tyler, The Creator - Call Me If You Get Lost: The Estate Sale (28058949)
# 3. Pino Daniele - Un Uomo In Blues (2229728)
# 4. The Cure - Disintegration (14677130)
# 5. Pink Floyd - The Dark Side of the Moon (19719631)
SEED_RELEASES = [169648, 28058949, 2229728, 14677130, 19719631]

# Liste semplificate per i dati fittizi degli utenti
FIRST_NAMES = ["Luca", "Giulia", "Marco", "Sofia", "Andrea"]
SURNAMES = ["Rossi", "Ferrari", "Bianchi", "Russo", "Conti"]
FORMATS = ["Vinile", "CD", "Cassetta"]
CONDITIONS = ["Nuovo", "Come nuovo", "Buono", "Discreto", "Rovinato"]
NOTES_POOL = [
    "Prima stampa originale", "Edizione limitata in vinile colorato", "Firmato dall'artista",
    "Condizioni della copertina leggermente usurate", "Include inserto fotografico originale",
    "Ristampa audiophile 180g", "Edizione speciale per il Record Store Day", "Copia promozionale",
    "Nessuna nota", None
]

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
            if bool(non_latin_pattern.search(parts[0])) and not bool(non_latin_pattern.search(parts[1])):
                return parts[1]
            if bool(non_latin_pattern.search(parts[1])) and not bool(non_latin_pattern.search(parts[0])):
                return parts[0]
            return parts[0]
    return title.strip()

def map_genre(genres, styles):
    terms = []
    if genres:
        terms.append(genres[0])
    if styles:
        terms.extend(styles[:2])
    unique = []
    for t in terms:
        if t not in unique:
            unique.append(t)
    return ", ".join(unique[:2]) if unique else "Unknown"

def get_itunes_cover_url(artist, album):
    if not artist or not album:
        return None
    url = "https://itunes.apple.com/search"
    params = {"term": f"{artist} {album}", "media": "music", "entity": "album", "limit": 5}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            
            def clean(s):
                return re.sub(r'[^a-z0-9]', '', s.lower()) if s else ""
                
            c_sought_artist = clean(artist)
            c_sought_album = clean(album)
            
            for r in results:
                c_res_artist = clean(r.get("artistName", ""))
                c_res_album = clean(r.get("collectionName", ""))
                
                if (c_sought_artist in c_res_artist or c_res_artist in c_sought_artist) and \
                   (c_sought_album in c_res_album or c_res_album in c_sought_album):
                    artwork = r.get("artworkUrl100")
                    if artwork:
                        return artwork.replace("100x100bb", "1000x1000bb")
    except Exception:
        pass
    return None

def main():
    if not os.path.exists(DATABASE_PATH):
        print(f"[!] Errore: File database '{DATABASE_PATH}' non trovato.")
        return

    print("====================================================")
    print("GrooveBox - Popolamento Database (Clean Real Data Seed)")
    print("====================================================")
    
    key = os.environ.get("DISCOGS_CONSUMER_KEY")
    secret = os.environ.get("DISCOGS_CONSUMER_SECRET")
    if not key or not secret:
        print("[!] Errore: Credenziali Discogs non impostate nel file .env!")
        return
        
    headers = {
        "User-Agent": "GrooveBoxSeed/1.0",
        "Authorization": f"Discogs key={key.strip()}, secret={secret.strip()}"
    }
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    try:
        # 1. Pulisci dati esistenti
        print("-> Pulizia delle tabelle (esclusi utenti di default)...")
        cursor.execute("DELETE FROM PHYSICAL_COPY")
        cursor.execute("DELETE FROM ALBUM_ARTIST")
        cursor.execute("DELETE FROM ALBUM")
        cursor.execute("DELETE FROM ARTIST")
        cursor.execute("DELETE FROM USER WHERE id_user > 2")
        conn.commit()
        
        # 2. Genera utenti collezionisti fittizi
        print(f"-> Generazione di {NUM_COLLECTORS} collezionisti...")
        password_hash = generate_password_hash("password123")
        user_ids = [1, 2] # admin (1) e test (2) preesistenti
        used_usernames = {"admin", "test"}
        
        for _ in range(NUM_COLLECTORS):
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
        print(f"   [OK] Utenti totali nel DB: {len(user_ids)}")
        
        # 3. Importa gli album reali dal set di release ID hardcoded
        print(f"-> Importazione di {len(SEED_RELEASES)} album reali da Discogs...")
        os.makedirs(COVERS_DIR, exist_ok=True)
        os.makedirs(ARTISTS_DIR, exist_ok=True)
        
        artist_id_map = {}
        album_ids = []
        album_artist_relations = []
        
        for release_id in SEED_RELEASES:
            print(f"   -> Recupero release ID {release_id}...")
            time.sleep(1.1) # Rispetta il rate limit di Discogs
            
            try:
                res = requests.get(f"https://api.discogs.com/releases/{release_id}", headers=headers, timeout=5)
                if res.status_code == 429:
                    print("      [!] Rate limit raggiunto, attesa 15s...")
                    time.sleep(15)
                    res = requests.get(f"https://api.discogs.com/releases/{release_id}", headers=headers, timeout=5)
                res.raise_for_status()
                data = res.json()
                
                title = clean_title(data.get("title", ""))
                year = data.get("year")
                if not year and data.get("released"):
                    year = int(data.get("released", "")[:4])
                    
                genre = map_genre(data.get("genres", []), data.get("styles", []))
                
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
                
                tracklist = []
                for track in data.get("tracklist", []):
                    if track.get("type_", "track") == "track":
                        tracklist.append({
                            "position": track.get("position", ""),
                            "title": track.get("title", ""),
                            "duration": track.get("duration", "")
                        })
                
                artists_data = data.get("artists", [])
                primary_artist_name = clean_artist_name(artists_data[0].get("name", "")) if artists_data else ""
                
                # Risoluzione copertina
                cover_url = get_itunes_cover_url(primary_artist_name, title)
                
                if not cover_url:
                    images = data.get("images", [])
                    if images:
                        primary_images = [img for img in images if img.get("type") == "primary"]
                        cover_url = primary_images[0].get("uri") if primary_images else images[0].get("uri")
                
                if not cover_url and data.get("master_id"):
                    master_id = data.get("master_id")
                    try:
                        m_res = requests.get(f"https://api.discogs.com/masters/{master_id}", headers=headers, timeout=5)
                        if m_res.status_code == 200:
                            m_images = m_res.json().get("images", [])
                            if m_images:
                                m_prim = [img for img in m_images if img.get("type") == "primary"]
                                cover_url = m_prim[0].get("uri") if m_prim else m_images[0].get("uri")
                    except Exception:
                        pass
                
                if not cover_url:
                    cover_url = data.get("thumb")
                    
                cover_filename = None
                if cover_url:
                    ext = "png" if ".png" in cover_url.lower() else "webp" if ".webp" in cover_url.lower() else "jpg"
                    cover_filename = f"album_discogs_{release_id}.{ext}"
                    filepath = os.path.join(COVERS_DIR, cover_filename)
                    if not os.path.exists(filepath):
                        img_res = requests.get(cover_url, headers=headers, timeout=5)
                        if img_res.status_code == 200:
                            with open(filepath, "wb") as f:
                                f.write(img_res.content)
                        else:
                            cover_filename = None
                
                creator_id = random.choice(user_ids)
                cursor.execute(
                    """INSERT INTO ALBUM (title, releaseYear, genre, coverPath, id_user, discogs_id, tracklist, label, catno, barcode, country)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (title, year, genre, cover_filename, creator_id, release_id, json.dumps(tracklist) if tracklist else None, label_name, catno, barcode, country)
                )
                album_id = cursor.lastrowid
                album_ids.append(album_id)
                
                associated_artist_ids = []
                for art in artists_data:
                    art_name = clean_artist_name(art.get("name", ""))
                    discogs_art_id = art.get("id")
                    
                    if art_name not in artist_id_map:
                        print(f"      -> Recupero dettagli artista {art_name}...")
                        time.sleep(1.1)
                        bio = ""
                        photo_filename = None
                        
                        try:
                            art_res = requests.get(f"https://api.discogs.com/artists/{discogs_art_id}", headers=headers, timeout=5)
                            if art_res.status_code == 200:
                                art_data = art_res.json()
                                bio = art_data.get("profile", "")
                                
                                art_images = art_data.get("images", [])
                                art_photo_url = None
                                if art_images:
                                    art_prim = [img for img in art_images if img.get("type") == "primary"]
                                    art_photo_url = art_prim[0].get("uri") if art_prim else art_images[0].get("uri")
                                    
                                if art_photo_url:
                                    photo_filename = f"artist_discogs_{discogs_art_id}.jpg"
                                    filepath = os.path.join(ARTISTS_DIR, photo_filename)
                                    if not os.path.exists(filepath):
                                        img_res = requests.get(art_photo_url, headers=headers, timeout=5)
                                        if img_res.status_code == 200:
                                            with open(filepath, "wb") as f:
                                                f.write(img_res.content)
                                        else:
                                            photo_filename = None
                        except Exception as e:
                            print(f"         [!] Errore artista {art_name}: {e}")
                            
                        cursor.execute(
                            "INSERT INTO ARTIST (name, discogs_id, biography, image_path) VALUES (?, ?, ?, ?)",
                            (art_name, discogs_art_id, bio, photo_filename)
                        )
                        artist_id_map[art_name] = cursor.lastrowid
                        
                    associated_artist_ids.append(artist_id_map[art_name])
                
                for artist_id in associated_artist_ids:
                    cursor.execute(
                        "INSERT INTO ALBUM_ARTIST (id_album, id_artist) VALUES (?, ?)",
                        (album_id, artist_id)
                    )
                    album_artist_relations.append((album_id, artist_id))
                    
                print(f"      [OK] Elaborato: {title} - {primary_artist_name}")
                
            except Exception as ex:
                print(f"   [!] Errore nel caricamento del dettaglio release {release_id}: {ex}")
                
        # 4. Genera copie fisiche reali (collegate ad album e utenti reali)
        print(f"-> Generazione di {NUM_COPIES} copie fisiche...")
        today = datetime.date.today()
        
        for _ in range(NUM_COPIES):
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
            
        conn.commit()
        print("\n====================================================")
        print("POPOLAMENTO COMPLETATO CON SUCCESSO!")
        print("====================================================")
        print(f"- Utenti totali nel DB: {len(user_ids)}")
        print(f"- Artisti totali nel DB: {len(artist_id_map)}")
        print(f"- Album inseriti a catalogo: {len(album_ids)}")
        print(f"- Relazioni Album-Artista inserite: {len(album_artist_relations)}")
        print(f"- Copie fisiche totali distribuite: {NUM_COPIES}")
        print("====================================================")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[!] ERRORE DURANTE IL SEEDING: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
