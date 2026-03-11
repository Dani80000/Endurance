import websockets, asyncio, json, eel, queue

RENDER_URL = "wss://secure-chat-bs75.onrender.com" 

async def chat_loop(websocket, user, msg_queue):
    eel.receiveMessageUI("SYSTEM", f"Connected to server as {user}", "General")()
    
    async def listen_for_messages():
        try:
            async for message in websocket:
                data = json.loads(message)
                sender = data.get("sender", "SYSTEM")
                content = data.get("message")
                channel = data.get("channel", "General")
                
                if sender != user:
                    eel.receiveMessageUI(sender, content)()
        except websockets.exceptions.ConnectionClosed:
            eel.receiveMessageUI("SYSTEM", "Server connection closed")()

    asyncio.create_task(listen_for_messages())

    try:
        while True:
            if not msg_queue.empty():
                msg_data = msg_queue.get()

                text = msg_data["msg"]
                channel = msg_data["channel"]

                if text == "/quit": break
                if not text.strip(): continue

                payload = {"user_id": user, "message": text, "channel": channel}
                await websocket.send(json.dumps(payload))
                eel.receiveMessageUI(user, text, channel)()
            
            await asyncio.sleep(0.1)
    finally:
        pass

async def main_loop(user, pw, action_type, msg_queue):
    eel.updateLoginStatus(f"Connecting...")()
    try:
        async with websockets.connect(RENDER_URL) as websocket:
            auth_data = {"action": action_type, "user_id": user, "password": pw, "channel": "General"}
            await websocket.send(json.dumps(auth_data))
            
            response = json.loads(await websocket.recv())
            
            if response.get("status") == "success":
                if action_type == "login":
                    eel.showChatWindow()()
                    history = response.get("history", [])
                    for msg in history:
                        eel.receiveMessageUI(msg.get('sender', 'User'), msg.get('message'), "General")()
                    
                    await chat_loop(websocket, user, msg_queue)
                else:
                    eel.updateLoginStatus("Account created! Now login.")()
            else:
                eel.updateLoginStatus(f"Failed: {response.get('message')}")()
    except Exception as e:
        eel.updateLoginStatus(f"Error: {e}")()

def run_client(user, pw, action_type, msg_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_loop(user, pw, action_type, msg_queue))