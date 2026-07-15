"""
GrooveBox - Data Access Layer per Importazione da Discogs
========================================================
Fornisce la logica centralizzata per importare album dal database Discogs.
"""

import os
from flask import current_app
from core.database import get_db
from utils.discogs import (
    get_release,
    get_artist,
    download_discogs_image
)
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
    Crea automaticamente l'artista/i se non presenti e ne scarica biografia/foto.
    Scarica la copertina e salva la tracklist.
    Ritorna la tupla: (album_id, was_existing)
    """
    conn = get_db()
    existing_album = conn.execute(
        "SELECT id_album FROM ALBUM WHERE discogs_id = ?",
        (discogs_id,)
    ).fetchone()
    
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
                        photo_ext = "jpg"
                        photo_filename = f"artist_discogs_{art_discogs_id}.{photo_ext}"
                        dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
                        if not os.path.exists(dest):
                            download_discogs_image(photo_url, dest)
                        
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
                    photo_ext = "jpg"
                    photo_filename = f"artist_discogs_{art_discogs_id}.{photo_ext}"
                    dest = os.path.join(current_app.config["ARTISTS_FOLDER"], photo_filename)
                    if not os.path.exists(dest):
                        download_discogs_image(photo_url, dest)
                    
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

    # Scarica la copertina
    cover_filename = None
    cover_url = release_info["cover_url"]
    if cover_url:
        try:
            # Riconosci l'estensione, di solito jpg o png da Discogs
            ext = "jpg"
            if ".png" in cover_url.lower():
                ext = "png"
            elif ".webp" in cover_url.lower():
                ext = "webp"
                
            cover_filename = f"album_discogs_{discogs_id}.{ext}"
            dest_cover = os.path.join(current_app.config["COVERS_FOLDER"], cover_filename)
            if not os.path.exists(dest_cover):
                download_discogs_image(cover_url, dest_cover)
        except Exception as e:
            current_app.logger.warning(f"Impossibile scaricare copertina da Discogs: {e}")

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
