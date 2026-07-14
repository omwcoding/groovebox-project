"""
GrooveBox - Utility Client per API Discogs
==========================================
Gestisce la comunicazione con l'API REST di Discogs per la ricerca di album e artisti,
il recupero dei dettagli delle release (inclusa la tracklist) e la mappatura dei generi.
"""

import requests
import os
from core.config import Config

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
        
    return formatted_results

def search_artists(query, limit=10):
    """
    Cerca artisti sul database di Discogs.
    """
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
        
    return formatted_results

def get_release(release_id):
    """
    Recupera i dettagli completi di una singola release tramite ID Discogs.
    Inclusi artisti, tracklist, anno di uscita ed immagini di copertina primarie.
    """
    url = f"https://api.discogs.com/releases/{release_id}"
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    data = response.json()
    
    # Estrae l'immagine di copertina primaria se disponibile
    cover_url = None
    images = data.get("images", [])
    if images:
        primary_images = [img for img in images if img.get("type") == "primary"]
        if primary_images:
            cover_url = primary_images[0].get("uri")
        else:
            cover_url = images[0].get("uri")
            
    # Se non c'è nelle images, proviamo la thumbnail principale
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
            
    return {
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

def get_artist(artist_id):
    """
    Recupera le informazioni dettagliate di un artista tramite ID Discogs.
    Inclusi biografia e foto del profilo.
    """
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
            
    return {
        "discogs_id": data.get("id"),
        "name": clean_artist_name(data.get("name", "")),
        "biography": data.get("profile", ""),
        "photo_url": photo_url
    }

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
    import re
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
            import re
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
