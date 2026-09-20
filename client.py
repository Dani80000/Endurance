import os
import websockets, asyncio, json, eel, queue

RENDER_URL = os.getenv("SECURECHAT_WS_URL", "ws://127.0.0.1:10000/ws")

def normalize_dm_channel(user1, user2):
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

async def chat_loop(websocket, user, msg_queue):
    eel.receiveMessageUI("SYSTEM", f"Connected to server as {user}", "General")()
    
    async def listen_for_messages():
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("action") == "history_update":
                    channel = data.get("channel", "General")
                    history = data.get("history", [])
                    eel.receiveHistoryUI(channel, history)()
                    continue
                
                sender = data.get("sender", "SYSTEM")
                content = data.get("message")
                channel = data.get("channel", "General")
                
                if sender != user:
                    eel.receiveMessageUI(sender, content, channel)()
        except websockets.exceptions.ConnectionClosed:
            eel.receiveMessageUI("SYSTEM", "Server connection closed", "General")()

    asyncio.create_task(listen_for_messages())

    try:
        while True:
            if not msg_queue.empty():
                msg_data = msg_queue.get()
                
                action = msg_data.get("action", "send_message")
                channel = normalize_channel_name(msg_data.get("channel", "General"))
                
                if action == "get_history":
                    payload = {"action": "get_history", "channel":channel}
                    await websocket.send(json.dumps(payload))
                    await asyncio.sleep(0.1)
                    continue

                text = msg_data.get("msg", "")
                
                if isinstance(text, str):
                    if text == "/quit": break
                    if not text.strip(): continue

                payload = {"action": "send_message", "user_id": user, "message": text, "channel": channel}
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
                    eel.receiveHistoryUI("General", history)()
                    
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
