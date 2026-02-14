#This file is used to store account credentials and create / delete accounts

import json, base64, os, secrets
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

FILE = "accounts.json"

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DK_LEN = 32

def load_accounts():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_accounts(account):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(account, f, indent=4)

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
    accounts = load_accounts()
    if user_id in accounts:
        print("User_id already exists")
        return False
    accounts[user_id] = password_hash
    save_accounts(accounts)
    print("Account created successfully")
    return True

def authenticate_account(user_id, password_plaintext):
    if not os.path.exists("accounts.json"):
        return False

    accounts = load_accounts()
    if user_id not in accounts:
        return False
    
    return verify_password(accounts[user_id], password_plaintext)


def find_account(user_id):
    return user_id in load_accounts()