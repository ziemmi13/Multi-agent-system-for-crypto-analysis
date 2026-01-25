import json
import uuid
from datetime import datetime, UTC
from root_agent.sub_agents.trader.tools.portfolio_manager import load_portfolio 

def format_trade_request(action: str, coin_id: str, coin_market_cap: float, symbol: str, quantity: float, entry_price: float,
                         stop_price: float, order_type: str, currency: str = "usd", rationale: str = ""):
    """Create a `TradeRequest` dict matching the agreed schema.

    Fields:
    - `action`: 'buy'|'sell'|'hold'
    - `coin_id`, `symbol`, `currency`
    - numeric fields are optional but recommended for validation by policy enforcer
    """
    
    portfolio_assets, full_portfolio_value_usd = load_portfolio()

    position_size_percent = (quantity * entry_price / float(full_portfolio_value_usd) * 100) if full_portfolio_value_usd else 0.0

    trade = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "action": action.lower(),
        "asset": {
            "symbol": symbol.lower(),
            "coin_id": coin_id.lower(),
            "coin_market_cap": coin_market_cap,
            "current_price_usd": entry_price if entry_price is not None else 0.0,
            "currency": currency.lower()
        },
        "position": {
            "quantity": quantity if quantity is not None else 0,
            "position_size_percent": position_size_percent if position_size_percent is not None else 0,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "order_type": order_type
        },
        "rationale": rationale,
    }

    trade_json = json.dumps(trade, separators=(',', ':'), sort_keys=False)

    return trade_json
