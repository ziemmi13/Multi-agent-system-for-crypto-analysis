from typing import List
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv
import pathlib
import asyncio
import random

# Load environment variables from root directory
root_dir = pathlib.Path(__file__).parent.parent.parent.parent
load_dotenv(root_dir / '.env')
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) #type: ignore

def parse_message_reactions(reactions):
    """
    Parses a Telethon MessageReactions object into a simple string.
    Example output: "❤: 6, 👍: 3, 🤡: 3, 🐳: 1"
    """
    if not reactions or not hasattr(reactions, 'results'):
        return "No reactions"

    reaction_strings = []
    
    # Each 'rc' is a ReactionCount object
    for rc in reactions.results:
        count = rc.count
        
        # Check if it is a standard emoji reaction
        if hasattr(rc.reaction, 'emoticon'):
            emoji = rc.reaction.emoticon
        # Check if it is a custom (Premium) emoji reaction
        elif hasattr(rc.reaction, 'document_id'):
            emoji = f"[CustomEmoji:{rc.reaction.document_id}]"
        else:
            emoji = ""
            
        reaction_strings.append(f"{emoji}: {count}")
    
    return ", ".join(reaction_strings)

async def get_channel_news(channel_handle, client, limit=5):
    try:
        news_items = []
        async for msg in client.iter_messages(channel_handle, limit=limit):
            id = msg.id
            date = msg.date
            message = msg.message
            views = msg.views
            forwards = msg.forwards
            reactions = parse_message_reactions(msg.reactions)
            comments = []
            if msg.replies and msg.replies.replies > 0: # msg.replies.replies is just the number of replies
                async for comment in client.iter_messages(channel_handle, reply_to=msg.id, limit=5):
                    if comment.text:
                        comments.append(comment.text) 

            news_item = (
                f"Date: {date}\n"
                f"Message: {message}\n"
                f"Views: {views}, Forwards: {forwards}, Reactions: {reactions}, Comments: {comments}\n"
            )
            
            news_items.append(news_item)

        return "\n---\n".join(news_items)

    except Exception as e:
        return f"Failed to fetch news: {str(e)}"

async def get_telegram_news(channels: List[str], limit: int = 5):
    """
    Fetch news from specified Telegram crypto channels.
    
    Args:
        channels: List of channel handles to fetch from. If None, uses all available channels.
        limit: Number of messages to fetch per channel (default: 5)
    
    Returns:
        Formatted string containing news from specified channels
    """
    
    if not client.is_connected():
        await client.connect()
    
    all_news = []
    for channel in channels:
        # Delay between scraping
        delay = random.uniform(1.5, 5)
        print(f"DEBUG: Waiting {delay:.2f}s before fetching {channel}...")
        await asyncio.sleep(delay)

        news = await get_channel_news(channel, client, limit=limit)
        all_news.append(f"Telegram channel: {channel}\n{news}")
    
    return "\n\n".join(all_news)
