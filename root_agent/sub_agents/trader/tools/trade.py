import requests
from datetime import datetime
import os

def make_a_trade(action: str, coin_id: str, symbol: str,  currency: str = "usd"):
    """Execute or record a trading instruction.

    - For 'buy' or 'sell' the function fetches the current price and logs the trade.
    - For 'hold' the function does NOT execute a trade; it records the HOLD decision via `log_trade`.
    Returns a dict with a summary or an error message.
    """

    coingecko_endpoint = "https://api.coingecko.com/api/v3"
    current_price_endpoint = f"{coingecko_endpoint}/simple/price?ids={coin_id}&vs_currencies={currency}"

    action_l = action.lower() if isinstance(action, str) else ""

    # Handle HOLD explicitly: do not attempt to execute a trade, just log the decision.
    if action_l == "hold":
        price = None
        try:
            resp = requests.get(current_price_endpoint, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            price = data.get(coin_id, {}).get(currency)
        except requests.RequestException:
            # price stays None if we couldn't fetch it; still log the HOLD
            price = None

        log_trade(coin_id, symbol, price if price is not None else 0.0, currency, action_l)
        return {"action": "hold", "coin": coin_id, "symbol": symbol, "price": price, "message": "HOLD recorded"}

    if action_l not in ("buy", "sell"):
        return {"error": "Unsupported action. Use 'buy', 'sell', or 'hold'."}

    try:
        response = requests.get(current_price_endpoint, timeout=5)
        response.raise_for_status()
        current_price_data = response.json()
        price = current_price_data.get(coin_id, {}).get(currency)
        if price is None:
            return {"error": "Price not available for the given coin/currency."}
    except requests.RequestException as exc:
        return {"error": f"Failed to fetch data: {exc}"}

    # Save trade to notebook
    log_trade(coin_id, symbol, price, currency, action_l)

    return {"coin": coin_id, "symbol": symbol, "price": price}

def log_trade(coin_id: str, symbol: str, price: float, currency: str, action: str):
    """Logs the trade action to a local file with a timestamp.
    Args:
        coin_id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin').
        symbol (str): The symbol of the cryptocurrency (e.g., 'btc').
        price (float): The price at which the trade was made.
        currency (str): The currency in which the price is denominated.
        action (str): The trade action ('buy', 'sell', or 'hold').
    """
    price_str = price if price is not None else "N/A"
    log_entry = f"{datetime.utcnow().isoformat()} - {action.upper()} - {coin_id} ({symbol}) at {price_str} {currency}\n"
    log_file_path = os.path.join(os.path.dirname(__file__), "trade_log.txt")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
    