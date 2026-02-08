import os
from dotenv import load_dotenv
import pathlib
from binance.client import Client
import requests

# 1. Setup
ALLOWED_ASSETS = {
    'USDT': 'usd', 
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

root_dir = pathlib.Path(__file__).parents[3]
load_dotenv(root_dir / '.env')

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)

def get_batch_prices(coin_ids_list, currency="usd"):
    """Fetches current prices for a list of CoinGecko IDs in the specified currency.
    Args:
        coin_ids_list (list): List of CoinGecko coin IDs.
        currency (str): The fiat currency to get prices in (default is 'usd').
    
    Returns:
        dict: A dictionary mapping coin IDs to their prices.
    """
    
    ids_string = ",".join(coin_ids_list)
    
    endpoint = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ids_string,
        'vs_currencies': currency
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        if response.status_code == 200:
            return response.json() 
        else:
            print(f"Error fetching prices: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Exception: {e}")
        return {}

def load_portfolio():
    """
    Loads and evaluates the user's portfolio from Binance.
    
    Returns:
        dict: A dictionary with asset details and their USD values.
        float: Total portfolio value in USD.
    """
    
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
        
        if asset in ALLOWED_ASSETS:
            # Initialize entry
            portfolio_assets[asset] = {
                "free": free,
                "locked": locked,
                "total": total,
                "price_usd": 0.0,
                "value_usd": 0.0
            }
            
            if asset == 'USDT':
                portfolio_assets[asset]["price_usd"] = 1.0
                portfolio_assets[asset]["value_usd"] = total
            else:
                coingecko_id = ALLOWED_ASSETS[asset]
                ids_to_fetch.append(coingecko_id)

    if ids_to_fetch:
        prices_data = get_batch_prices(ids_to_fetch)
        
        for asset, data in portfolio_assets.items():
            if asset == 'USDT': 
                continue # Already handled
            
            cg_id = ALLOWED_ASSETS.get(asset)
            # Check if we got a price for this ID
            if cg_id in prices_data and 'usd' in prices_data[cg_id]:
                price = prices_data[cg_id]['usd']
                portfolio_assets[asset]["price_usd"] = price
                portfolio_assets[asset]["value_usd"] = data["total"] * price
            else:
                print(f"Warning: No price found for {asset} ({cg_id})")
    
    # Calculate total portfolio value in USDT
    for asset, data in portfolio_assets.items():
        full_portfolio_value_usd += data["value_usd"]

    return portfolio_assets, full_portfolio_value_usd

def make_trade(symbol: str, side: str, quantity: float, order_type: str, 
               price: float, stop_price: float, time_in_force: str):
    """
    Places a trade order on Binance.
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTCUSDT').
        side (str): 'BUY' or 'SELL'.
        quantity (float): Amount to buy/sell.
        order_type (str): Type of order ('MARKET', 'LIMIT', 'STOP_LOSS', TAKE_PROFIT).
        price (float, optional): Price for LIMIT orders.
        stop_price (float, optional): Stop price for STOP_LOSS/TAKE_PROFIT orders.
        time_in_force (str, optional): Time in force for LIMIT orders ('GTC', 'IOC', etc.)."""
    
    order_type = order_type.upper()
    side = side.upper()
    
    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "recvWindow": 10000
    }
    
    if order_type == "MARKET":
        pass # No need for extra params

    elif order_type == "LIMIT":
        params["price"] = str(price)
        params["timeInForce"] = time_in_force

    elif order_type in ["STOP_LOSS", "TAKE_PROFIT"]:
        params["stopPrice"] = str(stop_price)

    # Execute the order
    try:
        order = client.create_order(**params)
        return order
    except Exception as e:
        print(f"Error placing order: {e}")
        return None