from core.errors import BadRequestError

def validate_json_payload(data, required_fields):
    """
    Verifica che il payload fornito non sia nullo e contenga tutti i campi
    richiesti (che non devono essere stringhe vuote o composte solo da spazi).
    
    In caso di validazione fallita, solleva automaticamente un BadRequestError (400).
    """
    if not data:
        raise BadRequestError("Nessun dato JSON fornito nel corpo della richiesta")
        
    for field in required_fields:
        val = data.get(field)
        # Se il campo non esiste o è None, oppure se è una stringa vuota dopo lo strip
        if val is None or (isinstance(val, str) and not val.strip()):
            raise BadRequestError(f"Il campo '{field}' è obbligatorio e non può essere vuoto")
