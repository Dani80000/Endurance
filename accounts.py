import json
import os
import hashlib

# File to store user data
ACCOUNTS_FILE = "accounts.json"

def hash_password(password):
    # Standard SHA-256 hashing
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
    Expects the password to ALREADY be hashed by server.py.
    """
    accounts = load_accounts()
    if user_id in accounts:
        return False
    
    # Store the hash directly
    accounts[user_id] = password_hash
    save_accounts(accounts)
    return True

def authenticate_account(user_id, password_plaintext):
    """
    Takes a PLAINTEXT password, hashes it, and compares to the stored hash.
    """
    accounts = load_accounts()
    if user_id not in accounts:
        return False
    
    # Hash the input to see if it matches the stored version
    input_hash = hash_password(password_plaintext)
    return accounts[user_id] == input_hash