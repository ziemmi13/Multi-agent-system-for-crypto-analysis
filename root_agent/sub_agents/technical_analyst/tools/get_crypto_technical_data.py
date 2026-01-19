from datetime import datetime
import requests
from typing import Dict, Any

def get_crypto_technical_data(coin_id: str, symbol: str,  currency: str = "usd"):
    """Fetches technical data for a given cryptocurrency from the CoinGecko API.
    Args:
        id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin').
        symbol (str): The symbol of the cryptocurrency (e.g., 'btc').
        currency (str, optional): The fiat currency to compare against (e.g., 'usd').
    Returns:
        Dict[str, Any]: A dictionary containing various technical data points.
    """

    coingecko_endpoint = f"https://api.coingecko.com/api/v3/"

    general_endpoints = {
        "global_data": f"{coingecko_endpoint}global",
    }

    specific_coin_endpoints = {
        "current_price": f"{coingecko_endpoint}/simple/price?ids={coin_id}&vs_currencies={currency}",
        "detailed_data_for_coin": f"{coingecko_endpoint}/coins/{coin_id}",
    }

    technical_data = {}
    for key, url in {**general_endpoints, **specific_coin_endpoints}.items():
        response = requests.get(url)
        if response.status_code == 200:
            technical_data[key] = response.json()
        else:
            technical_data[key] = {"error": f"Failed to fetch data from {url}"}
        
    formated_techinical_data = format_technical_data(technical_data, symbol)
    
    return formated_techinical_data

def format_technical_data(technical_data: Dict[str, Any], symbol: str) -> str:
    """Formats the technical data into a readable string.
    Args:
        technical_data (Dict[str, Any]): The technical data dictionary.
        symbol (str): The symbol of the cryptocurrency (e.g., 'btc').
    Returns:
        str: A formatted string representation of the technical data.
    """
    def _safe_get(d: Dict[str, Any], *keys, default="N/A") -> Any:
        """Safely traverse nested dicts using a sequence of keys.

        Example: _safe_get(obj, 'a', 'b', 'c') -> obj['a']['b']['c'] if present else default
        """
        cur = d if isinstance(d, dict) else {}
        for k in keys:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k, default)
            if cur is default:
                return default
        return cur

    # Market cap (global data)
    coin_total_market_cap = (
        _safe_get(technical_data, "global_data", "data", "total_market_cap", symbol)
        or "Not available"
    )
    coin_market_cap_percentage = (
        _safe_get(technical_data, "global_data", "data", "market_cap_percentage", symbol)
        or "Not available"
    )

    # Detailed coin-level data
    detailed_raw = technical_data.get("detailed_data_for_coin", {}) or {}
    detailed_fields = [
        "sentiment_votes_up_percentage",
        "sentiment_votes_down_percentage",
        "watchlist_portfolio_users",
        "market_cap_rank",
    ]
    detailed_data_for_coin = {k: detailed_raw.get(k, None) for k in detailed_fields}

    # Market data convenience
    market_data = detailed_raw.get("market_data", {}) or {}
    # Use currency-aware lookups where appropriate; keep existing symbol-based access for compatibility
    ath = market_data.get("ath", {}).get(symbol, "N/A")
    ath_change_percentage = market_data.get("ath_change_percentage", {}).get(symbol, "N/A")
    atl = market_data.get("atl", {}).get(symbol, "N/A")
    atl_change_percentage = market_data.get("atl_change_percentage", {}).get(symbol, "N/A")
    fully_diluted_valuation = market_data.get("fully_diluted_valuation", {}).get(symbol, "N/A")
    market_cap_fdv_ratio = market_data.get("market_cap_fdv_ratio", "N/A")

    # Price changes / supply
    high_24h = market_data.get("high_24h", {}).get(symbol, "N/A")
    low_24h = market_data.get("low_24h", {}).get(symbol, "N/A")
    price_change_24h = market_data.get("price_change_24h", "N/A")
    price_change_percentage_24h = market_data.get("price_change_percentage_24h", "N/A")
    price_change_percentage_7d = market_data.get("price_change_percentage_7d", "N/A")
    price_change_percentage_30d = market_data.get("price_change_percentage_30d", "N/A")

    total_supply = market_data.get("total_supply", "N/A")
    max_supply = market_data.get("max_supply", "N/A")
    circulating_supply = market_data.get("circulating_supply", "N/A")

    # Compose a readable multi-line output using a list of lines for clarity
    lines = [f"Research done for the coin with symbol: {symbol}", ""]
    lines.append("Current Price:")
    lines.append(str(technical_data.get("current_price", {})))
    lines.append("")
    lines.append("Total Market Cap:")
    lines.append(str(coin_total_market_cap))
    lines.append("")
    lines.append("Market Cap Percentage:")
    lines.append(str(coin_market_cap_percentage))
    lines.append("")
    lines.append("Detailed Data for Coin:")
    lines.append(str(detailed_data_for_coin))
    lines.append("")
    lines.append("Market Data Summary:")
    lines.append(f"ATH: {ath} (change {ath_change_percentage})")
    lines.append(f"ATL: {atl} (change {atl_change_percentage})")
    lines.append(f"Fully Diluted Valuation: {fully_diluted_valuation}")
    lines.append(f"Market Cap / FDV Ratio: {market_cap_fdv_ratio}")
    lines.append(f"High 24h: {high_24h} | Low 24h: {low_24h}")
    lines.append(f"Price change 24h: {price_change_24h} ({price_change_percentage_24h})")
    lines.append(f"Price change 7d: {price_change_percentage_7d}")
    lines.append(f"Price change 30d: {price_change_percentage_30d}")
    lines.append(f"Supply - total: {total_supply}, max: {max_supply}, circulating: {circulating_supply}")
    lines.append("")

    return "\n".join(lines)