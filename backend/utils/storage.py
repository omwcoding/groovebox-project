"""
Mint - Client di integrazione con Supabase Storage
=============================================================================
Fornisce le funzioni helper per caricare, eliminare e generare URL pubblici
per i file multimediali (copertine, foto artisti, avatar) su Supabase Storage.
"""

import requests
try:
    from core.config import Config
except ModuleNotFoundError:
    from config import Config

def upload_file(bucket, filename, file_bytes, content_type="application/octet-stream"):
    """
    Carica un file in formato bytes all'interno del bucket specificato.
    Usa l'opzione x-upsert per sovrascrivere eventuali file esistenti con lo stesso nome.
    """
    if not filename:
        return False
    url = f"{Config.SUPABASE_URL}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {Config.SUPABASE_ANON_KEY}",
        "apikey": Config.SUPABASE_ANON_KEY,
        "x-upsert": "true",
        "Content-Type": content_type
    }
    try:
        response = requests.post(url, headers=headers, data=file_bytes, timeout=10)
        if response.status_code != 200:
            print(f"[STORAGE ERROR] Status: {response.status_code}, Body: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[STORAGE ERROR] Eccezione durante il caricamento del file: {e}")
        return False

def get_public_url(bucket, filename):
    """
    Restituisce l'URL pubblico diretto per visualizzare il file memorizzato.
    """
    if not filename:
        return None
    return f"{Config.SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"

def delete_file(bucket, filename):
    """
    Rimuove un file dal bucket specificato.
    """
    if not filename:
        return False
    url = f"{Config.SUPABASE_URL}/storage/v1/object/{bucket}"
    headers = {
        "Authorization": f"Bearer {Config.SUPABASE_ANON_KEY}",
        "apikey": Config.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    data = {"prefixes": [filename]}
    try:
        response = requests.delete(url, headers=headers, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[STORAGE ERROR] Impossibile eliminare file: {e}")
        return False

def clear_bucket(bucket):
    """Rimuove tutti i file presenti in un bucket di Supabase Storage."""
    url_list = f"{Config.SUPABASE_URL}/storage/v1/object/list/{bucket}"
    headers = {
        "Authorization": f"Bearer {Config.SUPABASE_ANON_KEY}",
        "apikey": Config.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url_list, headers=headers, json={"prefix": "", "limit": 1000}, timeout=10)
        if response.status_code == 200:
            files = response.json()
            names = [f["name"] for f in files if "name" in f]
            if names:
                url_remove = f"{Config.SUPABASE_URL}/storage/v1/object/{bucket}"
                requests.delete(url_remove, headers=headers, json={"prefixes": names}, timeout=10)
            return True
    except Exception as e:
        print(f"[STORAGE ERROR] Impossibile pulire il bucket {bucket}: {e}")
    return False
