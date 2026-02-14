import os
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import accounts
import connections

app = FastAPI()

if not os.path.exists("messages"):
    os.makedirs("messages")

active_connections = set()
last_message_times = {} 
RATE_LIMIT_SECONDS = 1 

@app.get("/")
@app.head("/")
async def root():
    return {"status": "Live and waiting for connections"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("New client connected.")
    current_user = None
    
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
        if connections.connect(user_id, password):
            active_connections.add(websocket)
            current_user = user_id
            
            history = connections.join_channel(user_id, "General")
            
            await websocket.send_json({
                "status": "success", 
                "message": "Connected securely.",
                "history": history
            })
            
            for conn in active_connections:
                if conn != websocket:
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} joined the chat."})

            try:
                while True:
                    payload = await websocket.receive_json()
                    
                    current_time = time.time()
                    last_time = last_message_times.get(user_id, 0)
                    
                    if current_time - last_time < RATE_LIMIT_SECONDS:
                        await websocket.send_json({
                            "sender": "SYSTEM", 
                            "message": "You are typing too fast, Try again."
                        })
                        continue
                    
                    last_message_times[user_id] = current_time

                    payload["sender"] = user_id
                    
                    try:
                        connections.save_message_to_json(payload)
                    except: pass
                    
                    for conn in active_connections:
                        if conn != websocket:
                            await conn.send_json(payload)
                            
            except WebSocketDisconnect:
                print(f"{user_id} disconnected")
                active_connections.remove(websocket)
                if user_id in last_message_times:
                    del last_message_times[user_id]
                for conn in active_connections:
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} left."})
        else:
            await websocket.send_json({"status": "error", "message": "Login Failed"})

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
