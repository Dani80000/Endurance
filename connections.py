import json
import os
import accounts

def connect(user_id, password, channel="General", receiver_id=None):
    # Passes the plain password to accounts.py for verification
    if accounts.authenticate_account(user_id, password):
        return True
    return False

def save_message_to_json(payload):
    # Creates folder if Render wiped it
    if not os.path.exists("messages"):
        os.makedirs("messages")

    channel = payload.get("channel", "General")
    filename = f"messages/{channel}.json"
    
    history = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                history = json.load(file)
        except json.JSONDecodeError:
            history = []

    history.append(payload)

    with open(filename, "w") as file:
        json.dump(history, file, indent=4)

def join_channel(user_id, channel):
    filename = f"messages/{channel}.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []