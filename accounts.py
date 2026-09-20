# This file is used to store account credentials and create / delete accounts.

import base64
import logging
import secrets
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from storage_utils import atomic_write_json, read_json, update_json

FILE = "accounts.json"
logger = logging.getLogger("securechat.accounts")

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DK_LEN = 32

def load_accounts():
    return read_json(FILE, {})
    
def save_accounts(account):
    atomic_write_json(FILE, account)

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    kdf = Scrypt(salt=salt, length=_DK_LEN, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    dk = kdf.derive(password.encode("utf-8"))
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()

def verify_password(stored: str, password: str) -> bool:
    try:
        _, salt_b64, dk_b64 = stored.split("$", 2)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        kdf = Scrypt(salt=salt, length=_DK_LEN, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
        kdf.verify(password.encode(), expected)
        return True
    except Exception:
        return False

def create_account(user_id, password_hash):
    def add_account(accounts):
        if user_id in accounts:
            return False
        accounts[user_id] = password_hash
        return True

    created = update_json(FILE, {}, add_account)
    if created:
        logger.info("Account created for user=%s", user_id)
    else:
        logger.info("Account creation rejected because user already exists: user=%s", user_id)
    return created

def authenticate_account(user_id, password_plaintext):
    accounts = load_accounts()
    if user_id not in accounts:
        return False
    return verify_password(accounts[user_id], password_plaintext)

def find_account(user_id):
    return user_id in load_accounts()
