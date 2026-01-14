from get_telegram_news import get_telegram_news
import asyncio

if __name__== "__main__":
    # Example usage
    channels = ["bitcoin", "cointelegraph"]
    news = asyncio.run(get_telegram_news(channels, limit=3))
    print(news)