import os
from dotenv import load_dotenv
import pathlib
import requests

# Load environment variables from root directory
root_dir = pathlib.Path(__file__).parent
load_dotenv(root_dir / '.env')
API_KEY = os.getenv('CRYPTO_PANIC_API_KEY')

def get_news_from_cryptopanic(currency: str, filter: str = "hot") -> str:
    base_endpoint = "https://cryptopanic.com/api/developer/v2/posts/"

    params = {
        "auth_token": API_KEY,
        "currencies": currency,    # filter by crypto symbols
        "kind": "news",            # 'news' or 'media'
        "public": "true",          # only public posts
        "filter": filter            # optional: 'rising', 'hot', 'bullish', etc.
    }

    try:
        response = requests.get(base_endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"Error fetching news: {e}"

    results = data.get("results", [])
    if not results:
        return f"No news found for {currency}."

    output = []
    for post in results:
        title = post.get("title", "No title")
        url_ = post.get("url", "No URL provided")
        published = post.get("published_at", "Unknown time")
        output.append(f"{title}\n {url_}\n {published}\n")

    return "\n".join(output)