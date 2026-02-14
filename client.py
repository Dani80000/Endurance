from getpass import getpass
import accounts, websockets, asyncio, json

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

            if not msg.strip(): #for empty messages
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

    if choice == "c":
        pw_hash = accounts.hash_password(pw)
        if not accounts.create_account(user, pw_hash):
            print("Account already exists.")
            return
        print("Account locally created.")

    else:
        if not accounts.authenticate_account(user, pw):
            print("Invalid local login.")
            return

    print("\nLocally logged in as", user)
    print(f"Connecting to {RENDER_URL}...")
    try:
        async with websockets.connect(RENDER_URL) as websocket:
            login_data = {
                "user_id": user,
                "password": pw,
                "channel": "General"
            }
            await websocket.send(json.dumps(login_data))
            await chat_loop(websocket, user)
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass