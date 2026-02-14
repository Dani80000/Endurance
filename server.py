# server.py
import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

ACCOUNTS_FILE = "accounts.json"
STATUS_FILE = "status.json"
MESSAGES_DIR = "messages"

os.makedirs(MESSAGES_DIR, exist_ok=True)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

active_connections = {}   # user -> websocket
user_rooms = {}           # user -> room

@app.get("/")
async def root():
    return {"status": "alive"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    current_user = None

    try:
        while True:
            packet = await websocket.receive_json()

            user = packet.get("userID")
            pw_hash = packet.get("passwordHash")
            flag = packet.get("flag")
            data = packet.get("data")

            accounts = load_json(ACCOUNTS_FILE)

            # --- CREATE ---
            if flag == "create":
                if user in accounts:
                    await websocket.send_json({
                        "success": False,
                        "message": "Username already exists."
                    })
                else:
                    accounts[user] = pw_hash
                    save_json(ACCOUNTS_FILE, accounts)

                    await websocket.send_json({
                        "success": True,
                        "message": "Account created."
                    })

            # --- LOGIN ---
            elif flag == "login":
                if user not in accounts:
                    await websocket.send_json({
                        "success": False,
                        "message": "User does not exist."
                    })
                elif accounts[user] != pw_hash:
                    await websocket.send_json({
                        "success": False,
                        "message": "Incorrect password."
                    })
                else:
                    active_connections[user] = websocket
                    current_user = user

                    await websocket.send_json({
                        "success": True,
                        "message": "Login successful."
                    })

            # --- CONNECT ROOM ---
            elif flag == "connect":
                room = data
                room_file = os.path.join(MESSAGES_DIR, f"{room}.json")

                if not os.path.exists(room_file):
                    save_json(room_file, [])

                user_rooms[user] = room

                messages = load_json(room_file)

                await websocket.send_json({
                    "success": True,
                    "message": f"Connected to {room}",
                    "data": messages
                })

            # --- MESSAGE ---
            elif flag == "message":
                room = user_rooms.get(user)

                if not room:
                    await websocket.send_json({
                        "success": False,
                        "message": "Not connected to a room."
                    })
                    continue

                room_file = os.path.join(MESSAGES_DIR, f"{room}.json")
                messages = load_json(room_file)

                msg_obj = {
                    "user": user,
                    "message": data
                }

                messages.append(msg_obj)
                save_json(room_file, messages)

                # Broadcast
                for u, ws in active_connections.items():
                    if user_rooms.get(u) == room and u != user:
                        await ws.send_json({
                            "flag": "message",
                            "data": msg_obj
                        })

            # --- DISCONNECT ---
            elif flag == "disconnect":
                break

    except WebSocketDisconnect:
        pass
    finally:
        if current_user:
            active_connections.pop(current_user, None)
            user_rooms.pop(current_user, None)
