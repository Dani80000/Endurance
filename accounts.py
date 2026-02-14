import json
import os
import hashlib

ACCOUNTS_FILE = "accounts.json"

def hash_password(password):
    # This turns a password into a secure hash
    return hashlib.sha256(password.encode()).hexdigest()

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)

def create_account(user_id, password_hash):
    """
    STORES the hash directly. Does NOT hash it again.
    """
    accounts = load_accounts()
    if user_id in accounts:
        return False
    
    # Store the hash exactly as the server sent it
    accounts[user_id] = password_hash
    save_accounts(accounts)
    return True

def authenticate_account(user_id, password_plaintext):
    """
    Hashes the input once and checks it against the stored hash.
    """
    accounts = load_accounts()
    if user_id not in accounts:
        return False
    
    # Hash the input to see if it matches the stored version
    input_hash = hash_password(password_plaintext)
    
    # Check against the stored hash
    if accounts[user_id] == input_hash:
        return True
        
    return False