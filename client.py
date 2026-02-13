import asyncio
import json
from getpass import getpass

import websockets
import accounts

SERVER_URI = "ws://localhost:8765"

def format_line(payload: dict) -> str:
    sender = payload.get("sender") or payload.get("user_id") or payload.get("from") or "Unknown"
    msg = payload.get("message") or payload.get("msg") or payload.get("text") or ""

    if not isinstance(msg, str):
        msg = str(msg)

    return f'{sender}: "{msg}"'

def login_or_create_local() -> tuple[str, str] | tuple[None, None]:

    choice = input("(l)ogin or (c)reate account? ").strip().lower()
    user_id = input("Username: ").strip()
    password = getpass("Password (hidden): ")

    if not user_id:
        print("Username cannot be empty.")
        return None, None

    if choice.startswith("c"):
        pw_hash = accounts.hash_password(password)
        ok = accounts.create_account(user_id, pw_hash)
        if not ok:
            print("Account already exists.")
            return None, None
        print("Account created.")

    if not accounts.authenticate_account(user_id, password):
        print("Login failed.")
        return None, None

    return user_id, password

async def run_chat(user_id: str, password: str, channel: str = "General", receiver_id: str | None = None):
    async with websockets.connect(SERVER_URI) as ws:
        login_packet = {
            "user_id": user_id,
            "password": password,
            "channel": channel,
            "receiver_id": receiver_id,
        }
        await ws.send(json.dumps(login_packet))

        resp = json.loads(await ws.recv())
        if resp.get("status") != "success":
            print("Server rejected login:", resp.get("message", resp))
            return

        print(resp.get("message", "Connected."))
        print(f"Joined channel: {channel}")
        print("\n--- Chat ---")
        print('History (if any) will appear below. Type and press Enter. "/quit" to exit.\n')

        history_lines = []
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.25)
            except asyncio.TimeoutError:
                break
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if payload.get("status"):
                continue
            line = format_line(payload)
            history_lines.append(line)

        for line in history_lines:
            print(line)

        print("> ", end="", flush=True)

        async def receiver_loop():
            while True:
                raw = await ws.recv()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                line = format_line(payload)

                print("\n" + line)
                print("> ", end="", flush=True)

        async def input_loop():
            while True:
                msg = await asyncio.to_thread(input, "")
                msg = msg.strip()

                if msg == "/quit":
                    return

                if not msg:
                    print("> ", end="", flush=True)
                    continue

                print(format_line({"sender": user_id, "message": msg}))

                payload = {"message": msg}
                await ws.send(json.dumps(payload))
                print("> ", end="", flush=True)

        try:
            await asyncio.gather(receiver_loop(), input_loop())
        except websockets.ConnectionClosed:
            print("\nDisconnected from server.")
     
def main():
    user_id, password = login_or_create_local()
    if not user_id:
        return

    channel = input('Channel (default "General"): ').strip() or "General"

    try:
        asyncio.run(run_chat(user_id, password, channel=channel))
    except KeyboardInterrupt:
        print("\nGoodbye.")

if __name__ == "__main__":
    main()
