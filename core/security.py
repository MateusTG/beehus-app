from cryptography.fernet import Fernet
import os
import base64
from core.config import settings

def get_fernet():
    # Attempt to get the key from settings or env
    key = getattr(settings, "DATABASE_ENCRYPTION_KEY", None)
    if not key:
        # Fallback for dev, but should be set in production
        # In a real scenario, we might want to raise an error if not in dev mode
        key = os.getenv("DATABASE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    if isinstance(key, str):
        key = key.encode()
    
    return Fernet(key)

def encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    if not value:
        return ""
    f = get_fernet()
    return f.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    """Decrypt a Fernet token back to its original string value."""
    if not token:
        return ""
    f = get_fernet()
    try:
        return f.decrypt(token.encode()).decode()
    except Exception:
        # If decryption fails (e.g. invalid key or non-encrypted value), return empty
        # or handle as needed for the application
        return ""
