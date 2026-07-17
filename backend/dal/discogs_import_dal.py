"""
Mint - Data Access Layer per Importazione da Discogs
========================================================
Fornisce la logica centralizzata per importare album dal database Discogs nel database PostgreSQL e Supabase Storage.
"""

import os
import tempfile
from flask import current_app
from core.database import get_db
from utils.discogs import (
    get_release,
    get_artist,
    download_discogs_image,
    get_itunes_cover_url
)
from utils.storage import upload_file
from dal.album_dal import insert_album
from dal.artist_dal import (
    find_artist_by_discogs_id,
    find_artist_by_name,
    insert_artist,
    update_artist_discogs_info
)

def import_album_from_discogs(discogs_id: int, user_id: int) -> tuple[int, bool]:
    """
    Importa un album da Discogs nel catalogo globale.
    Crea automaticamente l'artista/i se non presenti e ne carica biografia/foto.
    Scarica la copertina e salva la tracklist.
    Ritorna la tupla: (album_id, was_existing)
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_album FROM albums WHERE discogs_id = %s;", (discogs_id,))
        existing_album = cursor.fetchone()
    finally:
        cursor.close()
    
    if existing_album:
        return existing_album["id_album"], True

    # Recupera dettagli release da Discogs
    release_info = get_release(discogs_id)

    # Risoluzione ed importazione degli artisti della release
    local_artist_ids = []
    for art in release_info["artists"]:
        art_discogs_id = art["discogs_id"]
        art_name = art["name"]
        
        # Cerca artista locale per ID Discogs
        local_art = find_artist_by_discogs_id(art_discogs_id)
        
        # Se non lo trova, prova per nome
        if not local_art:
            local_art = find_artist_by_name(art_name)
            
        if local_art:
            # Artista esistente
            art_id = local_art["id_artist"]
            # Se l'artista esistente non ha ancora le info Discogs collegate, le arricchiamo ora
            if not local_art["discogs_id"] or not local_art["biography"]:
                try:
                    art_details = get_artist(art_discogs_id)
                    bio = art_details.get("biography", "")
                    photo_url = art_details.get("photo_url")
                    photo_filename = None
                    
                    if photo_url:
                        photo_filename = f"artist_discogs_{art_discogs_id}.jpg"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp_path = tmp.name
                        try:
                            if download_discogs_image(photo_url, tmp_path):
                                with open(tmp_path, "rb") as f:
                                    upload_file("artists", photo_filename, f.read(), "image/jpeg")
                        finally:
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
                        
                    update_artist_discogs_info(art_id, art_discogs_id, bio, photo_filename)
                except Exception as ex:
                    # Non bloccante per l'importazione dell'album
                    current_app.logger.warning(f"Impossibile arricchire l'artista {art_name}: {ex}")
            
            local_artist_ids.append(art_id)
        else:
            # Artista non presente: lo creiamo recuperando i dettagli completi da Discogs
            try:
                art_details = get_artist(art_discogs_id)
                bio = art_details.get("biography", "")
                photo_url = art_details.get("photo_url")
                photo_filename = None
                
                if photo_url:
                    photo_filename = f"artist_discogs_{art_discogs_id}.jpg"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp_path = tmp.name
                    try:
                        if download_discogs_image(photo_url, tmp_path):
                            with open(tmp_path, "rb") as f:
                                upload_file("artists", photo_filename, f.read(), "image/jpeg")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    
                art_id = insert_artist(art_name, art_discogs_id, bio, photo_filename)
                local_artist_ids.append(art_id)
            except Exception as ex:
                # Fallback: crea l'artista solo col nome
                current_app.logger.warning(f"Errore caricamento dettagli artista {art_name}, uso fallback nome: {ex}")
                art_id = insert_artist(art_name, art_discogs_id)
                local_artist_ids.append(art_id)
                
    if not local_artist_ids:
        # Se non ci sono artisti nella release, inseriamo a nome di un artista ignoto
        unknown_art = find_artist_by_name("Unknown Artist")
        if unknown_art:
            local_artist_ids.append(unknown_art["id_artist"])
        else:
            art_id = insert_artist("Unknown Artist")
            local_artist_ids.append(art_id)

    # Scarica la copertina (prova prima iTunes ad alta risoluzione, fall-back su Discogs)
    cover_filename = None
    
    artist_name = ""
    if release_info.get("artists"):
        artist_name = release_info["artists"][0].get("name", "")
    elif release_info.get("artist_name"):
        artist_name = release_info["artist_name"]
        
    itunes_cover_url = get_itunes_cover_url(release_info["title"], artist_name)
    cover_url = itunes_cover_url or release_info["cover_url"]
    
    if cover_url:
        try:
            ext = "jpg"
            if ".png" in cover_url.lower():
                ext = "png"
            elif ".webp" in cover_url.lower():
                ext = "webp"
                
            cover_filename = f"album_discogs_{discogs_id}.{ext}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp_path = tmp.name
            try:
                if download_discogs_image(cover_url, tmp_path):
                    with open(tmp_path, "rb") as f:
                        mime = f"image/{'png' if ext == 'png' else 'jpeg'}"
                        upload_file("covers", cover_filename, f.read(), mime)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            current_app.logger.warning(f"Impossibile scaricare copertina (iTunes/Discogs): {e}")

    # Salva l'album nel DB locale
    album_id = insert_album(
        title=release_info["title"],
        release_year=release_info["release_year"],
        genre=release_info["genre"],
        artist_ids=local_artist_ids,
        creator_user_id=user_id,
        discogs_id=discogs_id,
        tracklist=release_info["tracklist"],
        cover_path=cover_filename,
        label=release_info.get("label"),
        catno=release_info.get("catno"),
        barcode=release_info.get("barcode"),
        country=release_info.get("country")
    )
    
    return album_id, False
