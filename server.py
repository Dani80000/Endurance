# server.py
import asyncio
import websockets
import os

async def handler(websocket):
    async for message in websocket:
        print(f"Received: {message}")

        # Capitalize message
        response = message.upper()

        await websocket.send(response)

async def main():
    print("Starting WebSocket server...")
    port = int(os.environ.get("PORT", 10000))

    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
