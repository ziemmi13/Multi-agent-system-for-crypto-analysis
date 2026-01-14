import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')

async def main():
    # StringSession() with no argument creates a brand new session
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("Check your Telegram app for the code!")
        # This will print a long string. COPY IT.
        print("\nYOUR_SESSION_STRING:\n")
        print(client.session.save())
        print("\n--- COPY THE STRING ABOVE ---")

if __name__ == '__main__':
    asyncio.run(main())