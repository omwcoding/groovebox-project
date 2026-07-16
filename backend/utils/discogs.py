"""
GrooveBox - Utility Client per API Discogs
==========================================
Gestisce la comunicazione con l'API REST di Discogs per la ricerca di album e artisti,
il recupero dei dettagli delle release (inclusa la tracklist) e la mappatura dei generi.
"""

import requests
import os
import json
import datetime
import re
from core.config import Config
from core.database import get_db

def _get_cached_response(key, max_age_hours):
    try:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT response_json, cached_at FROM discogs_cache WHERE cache_key = %s;",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                cached_at = datetime.datetime.fromisoformat(row["cached_at"])
                age = (datetime.datetime.now() - cached_at).total_seconds() / 3600
                if age <= max_age_hours:
                    return json.loads(row["response_json"])
        finally:
            cursor.close()
    except Exception:
        pass
    return None

def _set_cached_response(key, data):
    try:
        conn = get_db()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO discogs_cache (cache_key, response_json, cached_at)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (cache_key) 
                       DO UPDATE SET response_json = EXCLUDED.response_json, cached_at = EXCLUDED.cached_at;""",
                    (key, json.dumps(data), datetime.datetime.now().isoformat())
                )
    except Exception:
        pass

def _get_headers():
    """Genera gli header di autenticazione per le richieste a Discogs."""
    key = Config.DISCOGS_CONSUMER_KEY
    secret = Config.DISCOGS_CONSUMER_SECRET
    if not key or not secret:
        raise RuntimeError(
            "Credenziali Discogs non configurate. "
            "Imposta DISCOGS_CONSUMER_KEY e DISCOGS_CONSUMER_SECRET nel tuo file .env."
        )
    return {
        "User-Agent": "GrooveBoxApp/1.0",
        "Authorization": f"Discogs key={key.strip()}, secret={secret.strip()}"
    }

def search_releases(query, limit=10):
    """
    Cerca release/album sul database di Discogs.
    Ritorna una lista strutturata con id, titolo, anno, generi e immagine di copertina (thumbnail).
    """
    cache_key = f"search:album:{query}:{limit}"
    cached = _get_cached_response(cache_key, 1)
    if cached is not None:
        return cached

    url = "https://api.discogs.com/database/search"
    params = {
        "q": query,
        "type": "release",
        "per_page": limit
    }
    
    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
    
    formatted_results = []
    for r in results:
        # Il titolo in Discogs è solitamente "Artista - Titolo"
        title_full = r.get("title", "")
        artist_name = ""
        album_title = clean_title(title_full)
        
        if " - " in title_full:
            parts = title_full.split(" - ", 1)
            artist_name = parts[0].strip()
            album_title = clean_title(parts[1].strip())
            
        formatted_results.append({
            "discogs_id": r.get("id"),
            "title": album_title,
            "artist_name": artist_name,
            "year": int(r.get("year")) if r.get("year") else None,
            "genre": map_genre(r.get("genre", []), r.get("style", [])),
            "thumb": r.get("thumb")
        })
        
    _set_cached_response(cache_key, formatted_results)
    return formatted_results

def search_artists(query, limit=10):
    """
    Cerca artisti sul database di Discogs.
    """
    cache_key = f"search:artist:{query}:{limit}"
    cached = _get_cached_response(cache_key, 1)
    if cached is not None:
        return cached

    url = "https://api.discogs.com/database/search"
    params = {
        "q": query,
        "type": "artist",
        "per_page": limit
    }
    
    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
    
    formatted_results = []
    for r in results:
        formatted_results.append({
            "discogs_id": r.get("id"),
            "name": r.get("title"),
            "thumb": r.get("thumb")
        })
        
    _set_cached_response(cache_key, formatted_results)
    return formatted_results

def get_itunes_cover_url(artist, album):
    """
    Interroga l'API pubblica di iTunes per trovare la copertina dell'album.
    Valida il risultato e ritorna l'URL dell'artwork a 600x600 o None se non trovato.
    """
    if not artist or not album:
        return None
        
    def clean(s):
        if not s:
            return ""
        return re.sub(r'[^a-z0-9]', '', s.lower())
        
    url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist} {album}",
        "media": "music",
        "entity": "album",
        "limit": 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            c_sought_artist = clean(artist)
            c_sought_album = clean(album)
            
            for r in results:
                r_artist = r.get("artistName", "")
                r_album = r.get("collectionName", "")
                
                c_result_artist = clean(r_artist)
                c_result_album = clean(r_album)
                
                # Verifica corrispondenza autore e album
                artist_match = c_sought_artist in c_result_artist or c_result_artist in c_sought_artist
                album_match = c_sought_album in c_result_album or c_result_album in c_sought_album
                
                if artist_match and album_match:
                    artwork_url = r.get("artworkUrl100")
                    if artwork_url:
                        return artwork_url.replace("100x100bb", "1000x1000bb")
    except Exception:
        pass
    return None

def get_release(release_id):
    """
    Recupera i dettagli completi di una singola release tramite ID Discogs.
    Inclusi artisti, tracklist, anno di uscita ed immagini di copertina primarie.
    """
    cache_key = f"release:{release_id}"
    cached = _get_cached_response(cache_key, 24)
    if cached is not None:
        return cached

    url = f"https://api.discogs.com/releases/{release_id}"
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    data = response.json()
    
    # 1. Estrae l'artista primario e il titolo pulito per cercare su iTunes
    title = clean_title(data.get("title", ""))
    artists_data = data.get("artists", [])
    primary_artist = ""
    if artists_data:
        primary_artist = clean_artist_name(artists_data[0].get("name", ""))
        
    cover_url = get_itunes_cover_url(primary_artist, title)
    
    # 2. Se iTunes non la trova, proviamo la copertina specifica della Release (per supportare copertine deluxe/alternative)
    if not cover_url:
        images = data.get("images", [])
        if images:
            primary_images = [img for img in images if img.get("type") == "primary"]
            cover_url = primary_images[0].get("uri") if primary_images else images[0].get("uri")
    
    # 3. Se la Release specifica non ha immagini, proviamo la Master Release di Discogs
    if not cover_url and data.get("master_id"):
        master_id = data.get("master_id")
        try:
            master_url = f"https://api.discogs.com/masters/{master_id}"
            m_res = requests.get(master_url, headers=_get_headers(), timeout=5)
            if m_res.status_code == 200:
                m_data = m_res.json()
                m_images = m_data.get("images", [])
                if m_images:
                    m_prim = [img for img in m_images if img.get("type") == "primary"]
                    cover_url = m_prim[0].get("uri") if m_prim else m_images[0].get("uri")
        except Exception:
            pass
 
    # 4. Fallback finale sulla thumbnail
    if not cover_url:
        cover_url = data.get("thumb")
        
    # Estrazione tracklist
    tracklist = []
    for track in data.get("tracklist", []):
        # Filtriamo le tracce che hanno tipo traccia o sono canzoni effettive
        if track.get("type_", "track") == "track":
            tracklist.append({
                "position": track.get("position", ""),
                "title": track.get("title", ""),
                "duration": track.get("duration", "")
            })
            
    # Artisti associati
    artists = []
    for art in data.get("artists", []):
        artists.append({
            "discogs_id": art.get("id"),
            "name": clean_artist_name(art.get("name", ""))
        })
        
    # Mappatura del genere relazionata ai vincoli DDL di GrooveBox
    mapped_genre = map_genre(data.get("genres", []), data.get("styles", []))
    
    # Anno di rilascio
    release_year = data.get("year")
    if not release_year and data.get("released"):
        # Se 'year' è vuoto prova ad estrarlo da 'released' (Es: 1991-09-24)
        released_str = data.get("released", "")
        if len(released_str) >= 4 and released_str[:4].isdigit():
            release_year = int(released_str[:4])
 
    # Etichetta e numero di catalogo
    label_name = None
    catno = None
    labels = data.get("labels", [])
    if labels:
        label_name = clean_artist_name(labels[0].get("name", ""))
        catno = labels[0].get("catno")
 
    # Codice a barre
    barcode = None
    for ident in data.get("identifiers", []):
        if ident.get("type") == "Barcode":
            barcode = ident.get("value", "").strip().replace(" ", "")
            break
 
    # Paese
    country = data.get("country")
            
    result = {
        "discogs_id": data.get("id"),
        "title": clean_title(data.get("title")),
        "release_year": release_year,
        "genre": mapped_genre,
        "cover_url": cover_url,
        "tracklist": tracklist,
        "artists": artists,
        "label": label_name,
        "catno": catno,
        "barcode": barcode,
        "country": country
    }
    
    _set_cached_response(cache_key, result)
    return result

def get_artist(artist_id):
    """
    Recupera le informazioni dettagliate di un artista tramite ID Discogs.
    Inclusi biografia e foto del profilo.
    """
    cache_key = f"artist:{artist_id}"
    cached = _get_cached_response(cache_key, 24)
    if cached is not None:
        return cached

    url = f"https://api.discogs.com/artists/{artist_id}"
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    data = response.json()
    
    # Estrae l'immagine dell'artista
    photo_url = None
    images = data.get("images", [])
    if images:
        primary_images = [img for img in images if img.get("type") == "primary"]
        if primary_images:
            photo_url = primary_images[0].get("uri")
        else:
            photo_url = images[0].get("uri")
            
    result = {
        "discogs_id": data.get("id"),
        "name": clean_artist_name(data.get("name", "")),
        "biography": data.get("profile", ""),
        "photo_url": photo_url
    }
    
    _set_cached_response(cache_key, result)
    return result

def download_discogs_image(url, filepath):
    """
    Scarica un'immagine dai server Discogs (CDN) utilizzando gli header autenticati.
    Salva il file nel percorso specificato.
    """
    if not url:
        return False
        
    # Crea cartelle genitore se mancanti
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    response = requests.get(url, headers=_get_headers(), stream=True)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False

def clean_artist_name(name):
    """
    Pulisce i suffissi numerici aggiunti da Discogs per gli omonimi (es. 'Nirvana (2)' -> 'Nirvana').
    """
    if not name:
        return ""
    # Rimuove cose come " (2)" o " (15)" in coda al nome dell'artista
    return re.sub(r'\s*\(\d+\)$', '', name).strip()

def map_genre(genres, styles):
    """
    Combina il genere principale e lo stile di Discogs in una stringa pulita ed esatta.
    Esempio: ["Rock"], ["Alternative Rock", "Grunge"] -> "Rock, Alternative Rock"
    """
    terms = []
    if genres:
        terms.append(genres[0])
    if styles:
        # Prendi i primi due stili al massimo
        terms.extend(styles[:2])
    
    # Rimuovi duplicati mantenendo l'ordine
    unique_terms = []
    for t in terms:
        if t not in unique_terms:
            unique_terms.append(t)
            
    return ", ".join(unique_terms[:2]) if unique_terms else "Unknown"

def clean_title(title):
    """
    Pulisce i titoli degli album rimuovendo le traduzioni fornite da Discogs (es. "Wish You Were Here = 炎").
    Se rileva caratteri non latini (giapponesi, russi, cinesi) in una sola delle due parti separate da '=',
    preferisce la parte contenente solo caratteri latini.
    """
    if not title:
        return ""
    if " = " in title:
        parts = [p.strip() for p in title.split(" = ")]
        if len(parts) >= 2:
            # Pattern per caratteri cirillici, cinesi, giapponesi, coreani
            non_latin_pattern = re.compile(r'[\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff\u0400-\u04ff\u1100-\u11ff\uac00-\ud7af]')
            has_non_latin_0 = bool(non_latin_pattern.search(parts[0]))
            has_non_latin_1 = bool(non_latin_pattern.search(parts[1]))
            
            if has_non_latin_0 and not has_non_latin_1:
                return parts[1]
            if has_non_latin_1 and not has_non_latin_0:
                return parts[0]
            return parts[0]
    return title.strip()
