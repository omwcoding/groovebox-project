import os
import random
import datetime
import json
import re
import time
import requests
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Aggiunge la cartella padre (backend/) al path di sistema per consentire l'importazione dei moduli di backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from utils.storage import upload_file
from utils.discogs import get_itunes_cover_url

# ID reali di release Discogs da importare per il seeding
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

NUM_COLLECTORS = 3       # Numero di utenti collezionisti fittizi da creare (oltre ad admin e test)
NUM_COPIES = 10          # Numero totale di copie fisiche da distribuire tra le collezioni

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

# get_itunes_cover_url importata da utils.discogs

def main():
    print("====================================================")
    print("Mint - Popolamento Database PostgreSQL su Supabase")
    print("====================================================")
    
    from core.config import Config
    key = Config.DISCOGS_CONSUMER_KEY
    secret = Config.DISCOGS_CONSUMER_SECRET
    if not key or not secret:
        print("[!] Errore: Credenziali Discogs non impostate nel file .env!")
        return
        
    headers = {
        "User-Agent": "MintSeed/1.0",
        "Authorization": f"Discogs key={key.strip()}, secret={secret.strip()}"
    }
    
    conn = get_db()
    
    try:
        # 1. Pulisci dati esistenti
        print("-> Pulizia delle tabelle (esclusi utenti di default)...")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM physical_copies;")
                cursor.execute("DELETE FROM album_artists;")
                cursor.execute("DELETE FROM albums;")
                cursor.execute("DELETE FROM artists;")
                cursor.execute("DELETE FROM users WHERE username NOT IN ('admin', 'test');")
        
        # 2. Genera utenti collezionisti fittizi
        print(f"-> Generazione di {NUM_COLLECTORS} collezionisti...")
        password_hash = generate_password_hash("password123")
        
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id_user FROM users WHERE username IN ('admin', 'test');")
                user_ids = [row["id_user"] for row in cursor.fetchall()]
        used_usernames = {"admin", "test"}
        
        with conn:
            with conn.cursor() as cursor:
                for _ in range(NUM_COLLECTORS):
                    name = random.choice(FIRST_NAMES)
                    surname = random.choice(SURNAMES)
                    username = f"{name.lower()}.{surname.lower()}"
                    if username in used_usernames:
                        username = f"{username}{random.randint(10, 99)}"
                    used_usernames.add(username)
                    email = f"{username}@email.com"
                    
                    cursor.execute(
                        """INSERT INTO users (username, name, surname, email, password_hash, role)
                           VALUES (%s, %s, %s, %s, %s, 'collector') RETURNING id_user;""",
                        (username, name, surname, email, password_hash)
                    )
                    row = cursor.fetchone()
                    if row:
                        user_ids.append(row["id_user"])
        print(f"   [OK] Utenti totali nel DB: {len(user_ids)}")
        
        # 3. Importa gli album reali dal set di release ID hardcoded
        print(f"-> Importazione di {len(SEED_RELEASES)} album reali da Discogs...")
        
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
                cover_url = get_itunes_cover_url(title, primary_artist_name)
                
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
                    img_res = requests.get(cover_url, headers=headers, timeout=5)
                    if img_res.status_code == 200:
                        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                        upload_file("covers", cover_filename, img_res.content, mime)
                    else:
                        cover_filename = None
                
                creator_id = random.choice(user_ids)
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """INSERT INTO albums (title, release_year, genre, cover_path, id_user, discogs_id, tracklist, label, catno, barcode, country)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_album;""",
                            (title, year, genre, cover_filename, creator_id, release_id, json.dumps(tracklist) if tracklist else None, label_name, catno, barcode, country)
                        )
                        row = cursor.fetchone()
                        album_id = row["id_album"] if row else None
                
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
                                    img_res = requests.get(art_photo_url, headers=headers, timeout=5)
                                    if img_res.status_code == 200:
                                        upload_file("artists", photo_filename, img_res.content, "image/jpeg")
                                    else:
                                        photo_filename = None
                        except Exception as e:
                            print(f"         [!] Errore artista {art_name}: {e}")
                        
                        with conn:
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    "INSERT INTO artists (name, discogs_id, biography, image_path) VALUES (%s, %s, %s, %s) RETURNING id_artist;",
                                    (art_name, discogs_art_id, bio, photo_filename)
                                )
                                row_art = cursor.fetchone()
                                artist_id_map[art_name] = row_art["id_artist"] if row_art else None
                        
                    associated_artist_ids.append(artist_id_map[art_name])
                
                with conn:
                    with conn.cursor() as cursor:
                        for artist_id in associated_artist_ids:
                            cursor.execute(
                                "INSERT INTO album_artists (id_album, id_artist) VALUES (%s, %s);",
                                (album_id, artist_id)
                            )
                            album_artist_relations.append((album_id, artist_id))
                    
                print(f"      [OK] Elaborato: {title} - {primary_artist_name}")
                
            except Exception as ex:
                print(f"   [!] Errore nel caricamento del dettaglio release {release_id}: {ex}")
                
        # 4. Genera copie fisiche reali (collegate ad album e utenti reali)
        print(f"-> Generazione di {NUM_COPIES} copie fisiche...")
        today = datetime.date.today()
        
        with conn:
            with conn.cursor() as cursor:
                for _ in range(NUM_COPIES):
                    album_id = random.choice(album_ids)
                    user_id = random.choice(user_ids)
                    fmt = random.choice(FORMATS)
                    cond = random.choice(CONDITIONS)
                    days_ago = random.randint(0, 365)
                    added_date = (today - datetime.timedelta(days=days_ago)).isoformat()
                    notes = random.choice(NOTES_POOL)
                    
                    cursor.execute(
                        """INSERT INTO physical_copies (format, condition, added_date, personal_notes, id_user, id_album)
                           VALUES (%s, %s, %s, %s, %s, %s);""",
                        (fmt, cond, added_date, notes, user_id, album_id)
                    )
            
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
        print(f"\n[!] ERRORE DURANTE IL SEEDING: {e}")

if __name__ == "__main__":
    main()
