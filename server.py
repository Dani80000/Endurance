import os
import json
import time
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from collections import defaultdict
import uvicorn
import accounts
import connections

app = FastAPI()

if not os.path.exists("messages"):
    os.makedirs("messages")

active_connections = {}
last_message_times = {}
RATE_LIMIT_SECONDS = 1
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 900 #in seconds
MIN_PASSWORD_LENGTH = 8
MAX_USERNAME_LENGTH = 24
MAX_MESSAGE_LENGTH = 4000
MAX_FILE_DATA_LENGTH = 7_000_000
MAX_FILENAME_LENGTH = 120
login_attempts = defaultdict(list)
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")
SAFE_CHANNEL_RE = re.compile(r"^(General|dm_[a-z0-9_]{3,24}_[a-z0-9_]{3,24})$")
ALLOWED_ACTIONS = {"send_message", "get_history", "typing", "ping"}
BLOCKED_FILE_EXTENSIONS = {
    "ade", "adp", "apk", "app", "appx", "bat", "bin", "cmd", "com", "cpl",
    "dll", "dmg", "exe", "gadget", "hta", "ins", "iso", "jar", "js", "jse",
    "lnk", "msc", "msi", "msp", "mst", "ps1", "psm1", "reg", "scr", "sh",
    "sys", "vb", "vbe", "vbs", "ws", "wsc", "wsf", "wsh"
}

def is_locked_out(ip: str) -> bool:
    now = time.time()
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < LOCKOUT_TIME]
    return len(login_attempts[ip]) >= MAX_ATTEMPTS

def record_failed_attempt(ip: str):
    login_attempts[ip].append(time.time())


def validate_username(user_id: str) -> str | None:
    if not isinstance(user_id, str) or not user_id.strip():
        return "Username is required."

    if not USERNAME_RE.fullmatch(user_id):
        return "Username must be 3-24 characters and use only lowercase letters, numbers, and underscores."

    return None


def validate_password(password: str) -> str | None:
    if not isinstance(password, str) or not password:
        return "Password is required."

    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

    return None


def get_file_extension(filename: str) -> str:
    parts = filename.lower().split(".")
    return parts[-1] if len(parts) > 1 else ""


def has_suspicious_double_extension(filename: str) -> bool:
    parts = [part for part in filename.lower().split(".") if part]
    if len(parts) < 3:
        return False
    return parts[-1] in BLOCKED_FILE_EXTENSIONS or parts[-2] in BLOCKED_FILE_EXTENSIONS


def validate_channel(channel: str) -> str | None:
    if not isinstance(channel, str) or len(channel) > 80:
        return "Invalid channel."

    if not SAFE_CHANNEL_RE.fullmatch(channel):
        return "Invalid channel name."

    return None


def validate_message_payload(payload: dict, current_user: str) -> str | None:
    if not isinstance(payload, dict):
        return "Invalid payload."

    action = payload.get("action", "send_message")
    if action not in ALLOWED_ACTIONS:
        return "Unsupported action."

    channel = normalize_channel_name(payload.get("channel", "General"))
    channel_error = validate_channel(channel)
    if channel_error:
        return channel_error

    if channel.lower().startswith("dm_"):
        allowed_users = channel.lower().split("_")[1:]
        if current_user not in allowed_users:
            return "You are not part of this DM."

    if action in {"ping", "typing", "get_history"}:
        return None

    message = payload.get("message")
    if isinstance(message, str):
        if not message.strip():
            return "Message cannot be empty."
        if len(message) > MAX_MESSAGE_LENGTH:
            return f"Message is too long. Maximum is {MAX_MESSAGE_LENGTH} characters."
        return None

    if isinstance(message, dict) and message.get("type") == "file":
        filename = message.get("filename", "")
        data = message.get("data", "")

        if not isinstance(filename, str) or not filename.strip():
            return "File name is required."
        if len(filename) > MAX_FILENAME_LENGTH:
            return f"File name is too long. Maximum is {MAX_FILENAME_LENGTH} characters."
        if get_file_extension(filename) in BLOCKED_FILE_EXTENSIONS:
            return "Blocked potentially dangerous file type."
        if has_suspicious_double_extension(filename):
            return "Blocked suspicious double-extension filename."
        if not isinstance(data, str) or not data.startswith("data:"):
            return "Invalid file data."
        if len(data) > MAX_FILE_DATA_LENGTH:
            return "File data is too large."
        return None

    return "Invalid message."


async def send_validation_error(websocket: WebSocket, message: str, channel: str = "General"):
    await websocket.send_json({
        "sender": "SYSTEM",
        "message": message,
        "channel": channel
    })


async def broadcast_presence():
    users = sorted(set(active_connections.values()))
    for conn in list(active_connections.keys()):
        await conn.send_json({
            "action": "presence_update",
            "users": users,
            "channel": "General"
        })


async def broadcast_to_channel(payload, channel, current_user=None):
    if channel == "General":
        for conn in list(active_connections.keys()):
            await conn.send_json(payload)
        return

    if channel.lower().startswith("dm_"):
        allowed_users = channel.lower().split("_")[1:]
        if current_user and current_user not in allowed_users:
            return

        for conn, c_user_id in list(active_connections.items()):
            if c_user_id in allowed_users:
                await conn.send_json(payload)


@app.get("/")
@app.head("/")
async def root():
    return {
        "status": "Live and waiting for connections",
        "websocket": "/ws",
        "client": "Host the files in hosted/ on any static web host.",
    }


@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok"}


@app.get("/routes")
async def routes():
    return [
        {"path": route.path, "name": route.name, "type": route.__class__.__name__}
        for route in app.routes
    ]


def normalize_dm_channel(user1: str, user2: str) -> str:
    a, b = sorted([user1.strip().lower(), user2.strip().lower()])
    return f"dm_{a}_{b}"


def normalize_channel_name(channel: str) -> str:
    channel = (channel or "General").strip()

    if channel.lower() == "general":
        return "General"

    if channel.lower().startswith("dm_"):
        parts = channel.split("_")[1:]
        if len(parts) == 2:
            return normalize_dm_channel(parts[0], parts[1])
    return channel


@app.websocket("/")
async def websocket_endpoint_root(websocket: WebSocket):
    await handle_chat_websocket(websocket)


@app.websocket("/ws")
async def websocket_endpoint_ws(websocket: WebSocket):
    await handle_chat_websocket(websocket)


async def handle_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    print("New client connected.")
    current_user = None
    ip = (websocket.client.host if websocket.client else websocket.headers.get("x-forwarded-for", "unknown"))

    try:
        data = await websocket.receive_json()
        action = data.get("action", "login")
        user_id = data.get("user_id", "").strip().lower()
        password = data.get("password")

        username_error = validate_username(user_id)
        if username_error:
            await websocket.send_json({"status": "error", "message": username_error})
            return

        password_error = validate_password(password)
        if password_error:
            await websocket.send_json({"status": "error", "message": password_error})
            return
        
        if action == "create":
            print(f"Creating account for: {user_id}")
            pw_hash = accounts.hash_password(password)
            if accounts.create_account(user_id, pw_hash):
                await websocket.send_json({"status": "success", "message": "Account created on server."})
            else:
                await websocket.send_json({"status": "error", "message": "Account already exists."})
            return 

        print(f"Login attempt: {user_id}")
        if is_locked_out(ip):
            await websocket.send_json({"status": "error", "message": "You have been locked out. Try again later."})
            return
        if connections.connect(user_id, password):

            login_attempts[ip] = []
            active_connections[websocket] = user_id
            current_user = user_id
            
            history = connections.join_channel(user_id, "General")
            
            await websocket.send_json({
                "status": "success", 
                "message": "Connected securely.",
                "history": history
            })
            
            for conn in list(active_connections.keys()):
                if conn != websocket:
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} joined the chat.", "channel": "General"})
            await broadcast_presence()

            try:
                while True:
                    payload = await websocket.receive_json()
                    action = payload.get("action", "send_message")
                    channel = normalize_channel_name(payload.get("channel", "General"))
                    payload["channel"] = channel

                    validation_error = validate_message_payload(payload, current_user)
                    if validation_error:
                        await send_validation_error(websocket, validation_error, channel)
                        continue

                    if action == "ping":
                        await websocket.send_json({
                            "action": "pong",
                            "channel": channel
                        })
                        continue

                    if action == "typing":
                        await broadcast_to_channel({
                            "action": "typing",
                            "sender": current_user,
                            "channel": channel
                        }, channel, current_user)
                        continue

                    if action == "get_history":
                        history = connections.join_channel(current_user, channel)
                        await websocket.send_json({
                            "action": "history_update",
                            "channel": channel,
                            "history": history
                        })
                        continue

                    current_time = time.time()
                    last_time = last_message_times.get(user_id, 0)
                    
                    if current_time - last_time < RATE_LIMIT_SECONDS:
                        await websocket.send_json({
                            "sender": "SYSTEM", 
                            "message": "You are typing too fast, Try again.",
                            "channel": channel
                        })
                        continue
                    
                    last_message_times[user_id] = current_time

                    payload["sender"] = user_id
                    
                    try:
                        connections.save_message_to_json(payload)
                    except Exception as e:
                        print(f"Failed to save message: {e}")
                    
                    if channel == "General":
                        await broadcast_to_channel(payload, channel)
                    
                    elif channel.lower().startswith("dm_"):
                        await broadcast_to_channel(payload, channel, current_user)
                            
            except WebSocketDisconnect:
                print(f"{user_id} disconnected")
                if websocket in active_connections: del active_connections[websocket]
                if user_id in last_message_times:
                    del last_message_times[user_id]
                for conn in list(active_connections.keys()):
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} left.", "channel": "General"})
                await broadcast_presence()
        else:
            record_failed_attempt(ip)
            if is_locked_out(ip):
                await websocket.send_json({"status": "error", "message": "Try again later."})
            else:
                attempts_left = MAX_ATTEMPTS - len(login_attempts[ip])
                await websocket.send_json({
                    "status": "error",
                    "message": f"{attempts_left} attempts left."
         })

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if websocket in active_connections:
            del active_connections[websocket]
            await broadcast_presence()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
