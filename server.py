import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import accounts
import connections

app = FastAPI()

# Create messages directory if it doesn't exist to prevent crashes
if not os.path.exists("messages"):
    os.makedirs("messages")

# Set to keep track of active user connections
active_connections = set()

# --- HEALTH CHECK FIX ---
# This handles both GET and HEAD requests so Render knows we are alive
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
        # 1. Receive Auth Packet
        # We wait for the first message which MUST be login/create data
        data = await websocket.receive_json()
        
        action = data.get("action", "login")
        user_id = data.get("user_id", "").strip().lower()
        password = data.get("password")
        
        # 2. Handle Create Account
        if action == "create":
            print(f"Creating account for: {user_id}")
            pw_hash = accounts.hash_password(password)
            if accounts.create_account(user_id, pw_hash):
                await websocket.send_json({"status": "success", "message": "Account created on server."})
            else:
                await websocket.send_json({"status": "error", "message": "Account already exists."})
            # We close the connection after creation so they can login fresh
            return 

        # 3. Handle Login
        print(f"Login attempt: {user_id}")
        if connections.connect(user_id, password):
            active_connections.add(websocket)
            current_user = user_id
            
            # Load History for General chat
            history = connections.join_channel(user_id, "General")
            
            # Send Success + History in one packet
            await websocket.send_json({
                "status": "success", 
                "message": "Connected securely.",
                "history": history 
            })
            
            # Broadcast Join to everyone else
            for conn in active_connections:
                if conn != websocket:
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} joined the chat."})

            # 4. Main Chat Loop
            try:
                while True:
                    payload = await websocket.receive_json()
                    payload["sender"] = user_id
                    
                    # Attempt to save message (ignore errors to keep chat alive)
                    try:
                        connections.save_message_to_json(payload)
                    except: pass
                    
                    # Broadcast message to everyone (except sender)
                    for conn in active_connections:
                        if conn != websocket:
                            await conn.send_json(payload)
                            
            except WebSocketDisconnect:
                print(f"{user_id} disconnected")
                active_connections.remove(websocket)
                for conn in active_connections:
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} left."})
        else:
            await websocket.send_json({"status": "error", "message": "Login Failed"})

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # cleanup if needed
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)