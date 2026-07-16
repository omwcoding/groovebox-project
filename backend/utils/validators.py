"""
Mint - Utility di Validazione Input
========================================
Fornisce funzioni helper per la validazione formale dei payload JSON ricevuti
nelle richieste API, centralizzando i controlli sui campi obbligatori.
"""

from core.errors import BadRequestError

def validate_json_payload(data, required_fields):
    """
    Verifica la presenza e la non-vacuità dei campi richiesti in un payload JSON.
    Solleva un errore BadRequestError qualora un campo obbligatorio sia assente 
    o composto unicamente da spazi.
    """
    if not data:
        raise BadRequestError("Nessun dato JSON fornito nel corpo della richiesta")
        
    for field in required_fields:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            raise BadRequestError(f"Il campo '{field}' è obbligatorio e non può essere vuoto")
