import json
import os
import re
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
    safe_channel = safe_channel_name(channel)
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
    elif isinstance(message, dict) and message.get("type") == "file":
        file_data = message.get("data")
        if isinstance(file_data, str) and file_data.strip():
            payload_to_store["message"] = dict(message)
            payload_to_store["message"]["data"] = encrypt_message(file_data)
            payload_to_store["message"]["encrypted_data"] = True
            payload_to_store["encrypted"] = True

    history.append(payload_to_store)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

def join_channel(user_id, channel):
    safe_channel = safe_channel_name(channel)
    filename = f"messages/{safe_channel}.json"

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                history = json.load(file)

            decrypted_history = []
            for msg in history:
                msg_copy = dict(msg)

                if msg_copy.get("encrypted") is True:
                    stored_message = msg_copy.get("message", "")
                    if isinstance(stored_message, str) and stored_message.strip():
                        try:
                            msg_copy["message"] = decrypt_message(stored_message)
                        except Exception:
                            msg_copy["message"] = "[Unable to decrypt stored message]"
                    elif isinstance(stored_message, dict) and stored_message.get("type") == "file":
                        encrypted_file_data = stored_message.get("data", "")
                        if stored_message.get("encrypted_data") is True and isinstance(encrypted_file_data, str) and encrypted_file_data.strip():
                            msg_copy["message"] = dict(stored_message)
                            try:
                                msg_copy["message"]["data"] = decrypt_message(encrypted_file_data)
                                msg_copy["message"].pop("encrypted_data", None)
                            except Exception:
                                msg_copy["message"]["data"] = ""
                                msg_copy["message"]["download_error"] = "Unable to decrypt stored file"

                decrypted_history.append(msg_copy)

            return decrypted_history

        except json.JSONDecodeError:
            return []

    return []

def safe_channel_name(channel):
    channel = (channel or "General").strip()
    return re.sub(r"[^A-Za-z0-9_.-]", "_", channel)[:120] or "General"
