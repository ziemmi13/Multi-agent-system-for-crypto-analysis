from datetime import datetime, UTC
import json
import uuid

from root_agent.sub_agents.trader.tools.portfolio_manager import load_portfolio 
from root_agent.sub_agents.trader.tools.trade import get_trade_history 

def format_trade_request(action: str, coin_id: str, coin_market_cap: float, symbol: str, quantity: float, entry_price: float, stop_price: float, order_type: str, currency: str = "usd", rationale: str = "", volatility_1d: float = 0.0):
    """
    Creates a `TradeRequest` dict matching the required schema.
    
    Parameters:
        action: "buy", "sell", or "hold"
        coin_id: CoinGecko coin ID (e.g., "bitcoin")
        coin_market_cap: Current market capitalization of the coin in USD
        symbol: Coin symbol (e.g., "btc")
        quantity: Amount of the coin to trade
        entry_price: Price at which to enter the trade
        stop_price: Price at which to set the stop loss
        order_type: "market", "limit", "stop_loss", "take_profit"
        currency: Currency for the trade (default "usd")
        rationale: Explanation for the trade decision
        volatility_1d: 1-day annualized volatility (e.g. 50%)

    Returns:
    - A JSON string representing the TradeRequest object.

    """
    
    portfolio_assets, full_portfolio_value_usd = load_portfolio()

    position_size_percent = (quantity * entry_price / float(full_portfolio_value_usd) * 100) if full_portfolio_value_usd else 0.0

    # Get today's trade count
    trade_history_data = get_trade_history(limit=1)  # We only need the count, so limit=1 is fine
    today_trade_count = trade_history_data.get("today_trade_count", 0)

    trade = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "action": action.lower(),
        "asset": {
            "symbol": symbol.lower(),
            "coin_id": coin_id.lower(),
            "coin_market_cap": coin_market_cap,
            "current_price_usd": entry_price if entry_price is not None else 0.0,
            "volatility_1d": volatility_1d,
            "currency": currency.lower()
        },
        "position": {
            "quantity": quantity if quantity is not None else 0,
            "position_size_percent": position_size_percent if position_size_percent is not None else 0,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "order_type": order_type
        },
        "today_trade_count": today_trade_count,
        "rationale": rationale,
    }

    trade_json = json.dumps(trade, separators=(',', ':'), sort_keys=False)

    return trade_json
