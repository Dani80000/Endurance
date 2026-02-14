# client.py
import asyncio
from connections import send_message

async def main():
    user_input = input("Enter a message: ")

    response = await send_message(user_input)

    print("Server response:", response)

if __name__ == "__main__":
    asyncio.run(main())
