# client.py
import asyncio
import hashlib
import getpass
from connections import Connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

async def receive_loop(conn):
    while True:
        try:
            response = await conn.receive()

            if response.get("flag") == "message":
                msg = response["data"]
                print(f'\n{msg["user"]}: {msg["message"]}')
            else:
                print("\n", response.get("message"))

        except:
            print("Disconnected from server.")
            break

async def main():
    conn = Connection()
    await conn.connect()

    print("1) Login")
    print("2) Create Account")
    choice = input("> ")

    username = input("Username: ")
    password = getpass.getpass("Password: ")
    pw_hash = hash_password(password)

    flag = "login" if choice == "1" else "create"

    await conn.send({
        "userID": username,
        "passwordHash": pw_hash,
        "flag": flag,
        "data": ""
    })

    response = await conn.receive()

    print(response.get("message"))

    if not response.get("success"):
        return

    # Start background receiver
    asyncio.create_task(receive_loop(conn))

    while True:
        msg = input("> ")

        if msg.startswith("/connect"):
            parts = msg.split()
            if len(parts) < 2:
                print("Specify room.")
                continue

            await conn.send({
                "userID": username,
                "passwordHash": pw_hash,
                "flag": "connect",
                "data": parts[1]
            })

        elif msg.startswith("/quit"):
            await conn.send({
                "userID": username,
                "passwordHash": pw_hash,
                "flag": "disconnect",
                "data": ""
            })
            await conn.close()
            print("Goodbye.")
            break

        else:
            await conn.send({
                "userID": username,
                "passwordHash": pw_hash,
                "flag": "message",
                "data": msg
            })

if __name__ == "__main__":
    asyncio.run(main())
