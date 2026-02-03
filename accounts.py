#This file is used to store account credentials and create / delete accounts

import json
import os

FILE = "accounts.json"

def load_accounts():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)
    
def save_accounts(account):
    with open(FILE, "w") as f:
        json.dump(account, f, indent=4)

def create_account(user_id, password):
    accounts = load_accounts()
    if user_id in accounts:
        print("User_id already exists")
        return False
    accounts[user_id] = password
    save_accounts()
    print("Account created successfully")
    return True

def authenticate_account(user_id, password):
    accounts = load_accounts()
    if user_id not in accounts:
        return False
    if accounts[user_id] != password:
        return False
    return True

def find_account(user_id):
    accounts = load_accounts()
    if user_id in accounts:
        return True
    return False