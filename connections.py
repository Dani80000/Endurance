import json
import os
import accounts
from server_crypto import encrypt_message, decrypt_message

def connect(user_id, password, channel="General", receiver_id=None):
    if accounts.authenticate_account(user_id, password):
        return True
    return False

def save_message_to_json(payload):
    if not os.path.exists("messages"):
        os.makedirs("messages")

    channel = payload.get("channel", "General")
    safe_channel = channel.replace("/", "_").replace("\\", "_")
    filename = f"messages/{safe_channel}.json"
    
    history = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                history = json.load(file)
        except json.JSONDecodeError:
            history = []

    payload_to_store = dict(payload)

    message = payload_to_store.get("message")
    if isinstance(message, str) and message.strip():
        payload_to_store["message"] = encrypt_message(message)
        payload_to_store["encrypted"] = True

    history.append(payload_to_store)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

def join_channel(user_id, channel):
    safe_channel = channel.replace("/", "_").replace("\\", "_")
    filename = f"messages/{safe_channel}.json"

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                history = json.load(file)

            decrypted_history = []
            for msg in history:
                msg_copy = dict(msg)

                if msg_copy.get("encrypted") is True:
                    encrypted_text = msg_copy.get("message", "")
                    if isinstance(encrypted_text, str) and encrypted_text.strip():
                        try:
                            msg_copy["message"] = decrypt_message(encrypted_text)
                        except Exception:
                            msg_copy["message"] = "[Unable to decrypt stored message]"

                decrypted_history.append(msg_copy)

            return decrypted_history

        except json.JSONDecodeError:
            return []

    return []
