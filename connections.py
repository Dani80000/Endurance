# connections.py
import websockets
import asyncio
import json

RENDER_URL = "wss://secure-chat-bs75.onrender.com/ws"

class Connection:
    def __init__(self):
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(RENDER_URL)

    async def send(self, packet: dict):
        await self.websocket.send(json.dumps(packet))

    async def receive(self):
        response = await self.websocket.recv()
        return json.loads(response)

    async def close(self):
        if self.websocket:
            await self.websocket.close()
