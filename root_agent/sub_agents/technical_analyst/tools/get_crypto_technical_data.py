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
    detailed_data_for_coin = f"{coingecko_endpoint}/coins/{coin_id}"

    technical_data = {}
    
    # Get the filtered technical data from the endpoint
    try:
        coin_data = requests.get(detailed_data_for_coin).json()
        current_price = coin_data.get("market_data", {}).get("current_price", {}).get(f"{currency}", "N/A")
        
        # Sentiment
        sentiment_votes_up_percentage = coin_data.get("sentiment_votes_up_percentage", "N/A")
        sentiment_votes_down_percentage = coin_data.get("sentiment_votes_down_percentage", "N/A")
        watchlist_portfolio_users = coin_data.get("watchlist_portfolio_users", "N/A")
        
        # Market cap
        market_data = coin_data.get("market_data", {}) or {}
        market_cap = market_data.get("market_cap", {}).get(currency, "N/A")
        market_cap_rank = coin_data.get("market_cap_rank", "N/A")

        # Price changes 
        ath = {"ath_coin": market_data.get("ath", {}).get(symbol, "N/A"), 
               "ath_currency": market_data.get("ath", {}).get(currency, "N/A"),
               "ath_change_percentage_coin": market_data.get("ath_change_percentage", {}).get(symbol, "N/A"),
               "ath_change_percentage_currency": market_data.get("ath_change_percentage", {}).get(currency, "N/A")}

        atl = {"atl_coin": market_data.get("atl", {}).get(symbol, "N/A"),
               "atl_currency": market_data.get("atl", {}).get(currency, "N/A"),
               "atl_change_percentage_coin": market_data.get("atl_change_percentage", {}).get(symbol, "N/A"),
               "atl_change_percentage_currency": market_data.get("atl_change_percentage", {}).get(currency, "N/A")}

        fully_diluted_valuation = {"fully_diluted_valuation_coin": market_data.get("fully_diluted_valuation", {}).get(symbol, "N/A"),
                                   "fully_diluted_valuation_currency": market_data.get("fully_diluted_valuation", {}).get(currency, "N/A")}
        market_cap_fdv_ratio = market_data.get("market_cap_fdv_ratio", "N/A")
        
        total_volume = market_data.get("total_volume", {}).get(currency, "N/A")

        # Price changes
        high_24h = {"high_24h_coin": market_data.get("high_24h", {}).get(symbol, "N/A"),
                    "high_24h_currency": market_data.get("high_24h", {}).get(currency, "N/A")}
        low_24h = {"low_24h_coin": market_data.get("low_24h", {}).get(symbol, "N/A"),
                   "low_24h_currency": market_data.get("low_24h", {}).get(currency, "N/A")}
        price_change_24h = market_data.get("price_change_24h", "N/A"),
        price_change_percentage_24h = market_data.get("price_change_percentage_24h", "N/A")
        price_change_percentage_7d = market_data.get("price_change_percentage_7d", "N/A")
        price_change_percentage_14d = market_data.get("price_change_percentage_14d", "N/A")
        price_change_percentage_30d = market_data.get("price_change_percentage_30d", "N/A")
        price_change_percentage_60d = market_data.get("price_change_percentage_60d", "N/A")
        price_change_percentage_200d = market_data.get("price_change_percentage_200d", "N/A")
        price_change_percentage_1y = market_data.get("price_change_percentage_1y", "N/A")
        market_cap_change_24h = market_data.get("market_cap_change_24h", "N/A")
        market_cap_change_percentage_24h = market_data.get("market_cap_change_percentage_24h", "N/A")

        # Supply
        total_supply = market_data.get("total_supply", "N/A")
        max_supply = market_data.get("max_supply", "N/A")
        circulating_supply = market_data.get("circulating_supply", "N/A")

        technical_data = {
            "current_price": {currency: current_price},
            "sentiment_votes_up_percentage": sentiment_votes_up_percentage,
            "sentiment_votes_down_percentage": sentiment_votes_down_percentage,
            "watchlist_portfolio_users": watchlist_portfolio_users,
            "market_cap": {currency: market_cap},
            "market_cap_rank": market_cap_rank,
            "ath": ath,
            "atl": atl,
            "fully_diluted_valuation": fully_diluted_valuation,
            "market_cap_fdv_ratio": market_cap_fdv_ratio,
            "total_volume": {currency: total_volume},
            "high_24h": high_24h,
            "low_24h": low_24h,
            "price_change_24h": price_change_24h,
            "price_change_percentage_24h": price_change_percentage_24h,
            "price_change_percentage_7d": price_change_percentage_7d,
            "price_change_percentage_14d": price_change_percentage_14d,
            "price_change_percentage_30d": price_change_percentage_30d,
            "price_change_percentage_60d": price_change_percentage_60d,
            "price_change_percentage_200d": price_change_percentage_200d,
            "price_change_percentage_1y": price_change_percentage_1y,
            "market_cap_change_24h": market_cap_change_24h,
            "market_cap_change_percentage_24h": market_cap_change_percentage_24h,
            "total_supply": total_supply,
            "max_supply": max_supply,
            "circulating_supply": circulating_supply,
        }
    except Exception as e:
        technical_data = {"error": str(e)}

    return technical_data