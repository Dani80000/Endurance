# This script handles server related operations
import asyncio,connections, websockets, json, os

current_clients = set() # Keeps track of connected clients so messages are broadcasted to them TODO: Add safe removal when a client disconnects during send

async def handler(websocket): # Async will allow us to wait for messages without blocking
    print("New client connected. Waiting for login...")
    
    try: # This is here in order to void errors from getting bad data to prevent any failures TODO:(although this should be around things that can fail only)
        message = await websocket.recv() 
        data = json.loads(message)
        
        user_id = data.get("user_id")
        password = data.get("password")
        target_channel = data.get("channel") # ex: "General"
        target_dm = data.get("receiver_id")  # ex: "testUser"

        print(f"Login attempt received for: {user_id}")

        if connections.connect(user_id, password, channel=target_channel, receiver_id=target_dm):
            
            current_clients.add(websocket)
            print(f"User {user_id} successfully logged in!")
            
            await websocket.send(json.dumps({"status": "success", "message": "Connected securely."}))
            
            # load history
            history = connections.join_channel(user_id, target_channel or "General")
            # send history
            for msg in history:      
                await websocket.send(json.dumps(msg))     

            # Keep the connection open so they can chat
            async for msg in websocket:
                try:
                    payload = json.loads(msg)
                    payload["sender"] = user_id 
                    
                    connections.save_message_to_json(payload) 

                    for client in current_clients:
                        if client != websocket:
                            await client.send(json.dumps(payload))
                
                except json.JSONDecodeError:
                    print(f"Received non-JSON message from {user_id}")
                
        else:
            print(f"User {user_id} failed login.")
            await websocket.send(json.dumps({"status": "error", "message": "Login Failed"}))
    
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        if websocket in current_clients:
            current_clients.remove(websocket)

async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"The server is running on port {port}")
        await asyncio.Future()  # Run forever

#safeguard to run the file directly vs importing
if __name__ == "__main__":
    asyncio.run(main()) 