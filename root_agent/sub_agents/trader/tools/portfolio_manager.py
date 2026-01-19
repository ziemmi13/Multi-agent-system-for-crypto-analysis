import os
from dotenv import load_dotenv
import pathlib
from binance.client import Client


root_dir = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
load_dotenv(root_dir / '.env')

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)

def load_portfolio():
    account_info = client.get_account()
    return account_info

def make_trade():
    pass
