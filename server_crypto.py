import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

key = os.getenv("MESSAGE_ENCRYPTION_KEY")
if not key:
    raise ValueError("MESSAGE_ENCRYPTION_KEY is not set in .env")

cipher = Fernet(key.encode("utf-8"))

def encrypt_message(message: str) -> str:
    return cipher.encrypt(message.encode("utf-8")).decode("utf-8")

def decrypt_message(token: str) -> str:
    return cipher.decrypt(token.encode("utf-8")).decode("utf-8")