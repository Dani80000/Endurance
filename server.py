# server.py
import os
from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "alive"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        message = await websocket.receive_text()
        print("Received:", message)

        response = message.upper()
        await websocket.send_text(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
