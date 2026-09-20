from cryptography.fernet import Fernet
from config import settings

key = settings.fernet_key
if not key:
    raise ValueError("FERNET_KEY is not set in .env")

cipher = Fernet(key.encode("utf-8"))

def encrypt_message(message: str) -> str:
    return cipher.encrypt(message.encode("utf-8")).decode("utf-8")

def decrypt_message(token: str) -> str:
    return cipher.decrypt(token.encode("utf-8")).decode("utf-8")
