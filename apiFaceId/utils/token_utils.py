# utils/token_utils.py

import jwt
from django.conf import settings
from jwt.exceptions import InvalidTokenError

def decode_token(token: str):
    """
    Decodifica un token JWT y retorna los datos del payload.
    """
    try:
        # Asegúrate de usar la misma clave secreta con la que se firmó el token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except InvalidTokenError:
        return None
