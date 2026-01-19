import os
from dotenv import load_dotenv
import pathlib
from binance.client import Client
import requests

# 1. Setup
ALLOWED_ASSETS = {
    'USD': 'usd', 
    'BNB': 'binancecoin', 
    'BTC': 'bitcoin', 
    'ETH': 'ethereum', 
    'LTC': 'litecoin', 
    'TRX': 'tron', 
    'XRP': 'ripple', 
    'ADA': 'cardano', 
    'SOL': 'solana', 
    'DOGE': 'dogecoin', 
    'PEPE': 'pepe'
}

root_dir = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
load_dotenv(root_dir / '.env')

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)

def get_batch_prices(coin_ids_list, currency="usd"):
    # Join IDs with commas: "bitcoin,ethereum,solana"
    ids_string = ",".join(coin_ids_list)
    
    endpoint = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ids_string,
        'vs_currencies': currency
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json() 
        else:
            print(f"Error fetching prices: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Exception: {e}")
        return {}

def load_portfolio():
    account_info = client.get_account()
    balances = account_info.get("balances", [])
    
    portfolio_assets = {}
    ids_to_fetch = []
    full_portfolio_value_usd = 0.0
    
    # Step A: Filter assets and prepare the list of IDs to fetch
    for balance in balances:
        asset = balance.get("asset", "")
        free = float(balance.get("free", 0.0))
        locked = float(balance.get("locked", 0.0))
        total = free + locked
        
        if total > 0 and asset in ALLOWED_ASSETS:
            # Initialize entry
            portfolio_assets[asset] = {
                "free": free,
                "locked": locked,
                "total": total,
                "price_usd": 0.0,
                "value_usd": 0.0
            }
            
            if asset == 'USD':
                portfolio_assets[asset]["price_usd"] = 1.0
                portfolio_assets[asset]["value_usd"] = total
            else:
                coingecko_id = ALLOWED_ASSETS[asset]
                ids_to_fetch.append(coingecko_id)

    if ids_to_fetch:
        prices_data = get_batch_prices(ids_to_fetch)
        
        for asset, data in portfolio_assets.items():
            if asset == 'USD': 
                continue # Already handled
            
            cg_id = ALLOWED_ASSETS.get(asset)
            # Check if we got a price for this ID
            if cg_id in prices_data and 'usd' in prices_data[cg_id]:
                price = prices_data[cg_id]['usd']
                portfolio_assets[asset]["price_usd"] = price
                portfolio_assets[asset]["value_usd"] = data["total"] * price
            else:
                print(f"Warning: No price found for {asset} ({cg_id})")
    
    # Calculate total portfolio value in USD
    for asset, data in portfolio_assets.items():
        full_portfolio_value_usd += data["value_usd"]

    return portfolio_assets, full_portfolio_value_usd

def make_trade():
    pass
