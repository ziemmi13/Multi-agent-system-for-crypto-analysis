import json
import uuid
from datetime import datetime
from .load_portfolio import load_portfolio 

def format_trade_request(action: str, coin_id: str, symbol: str, quantity: float, entry_price: float,
                         target_exit_price: float, stop_loss_price: float,
                         order_type: str, currency: str = "usd", rationale: str = ""):
    """Create a `TradeRequest` dict matching the agreed schema.

    Fields:
    - `action`: 'buy'|'sell'|'hold'
    - `coin_id`, `symbol`, `currency`
    - numeric fields are optional but recommended for validation by policy enforcer
    """
    
    portfolio = load_portfolio()
    total_portfolio_value_usd = portfolio.get("total_portfolio_value_usd", 0.0)

    position_size_percent = (quantity * entry_price / total_portfolio_value_usd * 100) if total_portfolio_value_usd else 0.0

    trade = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action.lower(),
        "asset": {
            "symbol": symbol.lower(),
            "coin_id": coin_id.lower(),
            "current_price_usd": entry_price if entry_price is not None else 0.0,
            "currency": currency.lower()
        },
        "position": {
            "quantity": quantity if quantity is not None else 0,
            "position_size_percent": position_size_percent if position_size_percent is not None else 0,
            "entry_price": entry_price,
            "target_exit_price": target_exit_price,
            "stop_loss_price": stop_loss_price,
            "order_type": order_type
        },
        "rationale": rationale,
        "risk_metrics": {}
    }

    trade_json = json.dumps(trade, separators=(',', ':'), sort_keys=False)

    return trade_json