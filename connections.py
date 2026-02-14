# connections.py
import asyncio
import websockets

RENDER_URL = "wss://secure-chat-bs75.onrender.com"

async def send_message(message: str) -> str:
    async with websockets.connect(RENDER_URL) as websocket:
        await websocket.send(message)
        response = await websocket.recv()
        return response
