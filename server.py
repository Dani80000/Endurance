import os, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import accounts  # Make sure you have your accounts.py file next to this
import connections # Make sure connections.py is also there

app = FastAPI()

# Create messages directory if it doesn't exist
if not os.path.exists("messages"):
    os.makedirs("messages")

active_connections = set()

@app.get("/")
async def get():
    return {"status": "Live and waiting for connections"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("New client connected.")
    
    try:
        # 1. Receive Auth Packet
        data = await websocket.receive_json()
        
        action = data.get("action", "login")
        user_id = data.get("user_id", "").strip().lower()
        password = data.get("password")
        
        # 2. Handle Create
        if action == "create":
            print(f"Creating account for: {user_id}")
            pw_hash = accounts.hash_password(password)
            if accounts.create_account(user_id, pw_hash):
                await websocket.send_json({"status": "success", "message": "Account created on server."})
            else:
                await websocket.send_json({"status": "error", "message": "Account already exists."})
            return # Close connection after create

        # 3. Handle Login
        print(f"Login attempt: {user_id}")
        if connections.connect(user_id, password):
            active_connections.add(websocket)
            
            # Load History
            history = connections.join_channel(user_id, "General")
            
            # Send Success + History in one packet
            await websocket.send_json({
                "status": "success", 
                "message": "Connected securely.",
                "history": history # Sending history right here
            })
            
            # Broadcast Join
            for conn in active_connections:
                if conn != websocket:
                    await conn.send_json({"sender": "SYSTEM", "message": f"{user_id} joined the chat."})

            # 4. Chat Loop
            try:
                while True:
                    payload = await websocket.receive_json()
                    payload["sender"] = user_id
                    
                    # Save Message
                    try:
                        connections.save_message_to_json(payload)
                    except: pass
                    
                    # Broadcast
                    for conn in active_connections:
                        if conn != websocket:
                            await conn.send_json(payload)
                            
            except WebSocketDisconnect:
                print(f"{user_id} disconnected")
                active_connections.remove(websocket)
        else:
            await websocket.send_json({"status": "error", "message": "Login Failed"})

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)