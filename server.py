import os
import json
import time
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
login_attempts = defaultdict(list)

def is_locked_out(ip: str) -> bool:
    now = time.time()
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < LOCKOUT_TIME]
    return len(login_attempts[ip]) >= MAX_ATTEMPTS

def record_failed_attempt(ip: str):
    login_attempts[ip].append(time.time())


@app.get("/")
@app.head("/")
async def root():
    return {
        "status": "Live and waiting for connections",
        "websocket": "/",
        "client": "Host the files in hosted/ on any static web host.",
    }


@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok"}


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
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("New client connected.")
    current_user = None
    ip = (websocket.client.host if websocket.client else websocket.headers.get("x-forwarded-for", "unknown"))

    try:
        data = await websocket.receive_json()
        action = data.get("action", "login")
        user_id = data.get("user_id", "").strip().lower()
        password = data.get("password")
        
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

            try:
                while True:
                    payload = await websocket.receive_json()
                    action = payload.get("action", "send_message")
                    channel = normalize_channel_name(payload.get("channel", "General"))
                    payload["channel"] = channel

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
                        for conn in list(active_connections.keys()):
                            await conn.send_json(payload)
                    
                    elif channel.lower().startswith("dm_"):
                        allowed_users = channel.lower().split("_")[1:]

                        if current_user not in allowed_users:
                            await websocket.send_json({
                                "sender": "SYSTEM",
                                "message": "You are not part of this DM.",
                                "channel": channel
                            })
                            continue

                        for conn, c_user_id in list(active_connections.items()):
                            if c_user_id in allowed_users:
                                await conn.send_json(payload)
                            
            except WebSocketDisconnect:
                print(f"{user_id} disconnected")
                if websocket in active_connections: del active_connections[websocket]
                if user_id in last_message_times:
                    del last_message_times[user_id]
                for conn in list(active_connections.keys()):
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} left.", "channel": "General"})
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
        if websocket in active_connections: del active_connections[websocket]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
