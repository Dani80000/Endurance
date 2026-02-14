from getpass import getpass
import accounts, websockets, asyncio, json

# NOTE: No "/ws" at the end because FastAPI is listening on "/"
RENDER_URL = "wss://secure-chat-bs75.onrender.com" 

def prompt_auth():
    while True:
        choice = input("(l)ogin or (c)reate account? ").lower()
        if choice in ("l", "c"):
            return choice

async def chat_loop(websocket, user):
    print(f"\nConnected to server as {user}")
    print("Type /quit to exit\n")
    
    async def listen_for_messages():
        try:
            async for message in websocket:
                data = json.loads(message)
                sender = data.get("sender", "SYSTEM")
                content = data.get("message")
                
                if sender != user:
                    print(f"\r[{sender}]: {content}\n> ", end="")
        except websockets.exceptions.ConnectionClosed:
            print("\nServer connection closed")

    listener_task = asyncio.create_task(listen_for_messages())

    try:
        while True:
            msg = await asyncio.to_thread(input, "> ")
            if msg == "/quit":
                break

            if not msg.strip():
                continue

            payload = {
                "user_id": user,
                "message": msg,
                "channel": "General"
            }
            await websocket.send(json.dumps(payload))
    finally:
        listener_task.cancel()

async def main():
    print("=== Secure Chat Client ===")
    choice = prompt_auth()

    user = input("Username: ").strip().lower()
    pw = getpass("Password: ")

    print(f"\nConnecting to {RENDER_URL}...")
    try:
        async with websockets.connect(RENDER_URL) as websocket:
            
            action_type = "login" if choice == "l" else "create"

            auth_data = {
                "action": action_type,
                "user_id": user,
                "password": pw,
                "channel": "General"
            }
            await websocket.send(json.dumps(auth_data))
            
            response_json = await websocket.recv()
            response = json.loads(response_json)
            
            print(f"[SYSTEM]: {response.get('message')}")
            
            if response.get("status") == "success":
                if choice == "l":
                    # PRINT HISTORY HERE
                    history = response.get("history", [])
                    if history:
                        print("\n--- Recent Messages ---")
                        for msg in history:
                            print(f"[{msg.get('sender', 'User')}]: {msg.get('message')}")
                        print("-----------------------\n")
                    
                    await chat_loop(websocket, user)
                else:
                    print("Account created successfully on Server")
            else:
                print("Connection closed due to error")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass