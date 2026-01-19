import json
import uuid
from datetime import datetime, UTC
from root_agent.sub_agents.trader.tools.portfolio_manager import load_portfolio 

def calculate_portfolio_value(portfolio: dict) -> float:
    """
    Calculate total portfolio value in USD.
    
    Sums up all free balances. For stablecoins (USDT, USDC, DAI, etc.), 
    assumes 1:1 USD value. For other assets, this is a simplified calculation.
    
    Args:
        portfolio (dict): Portfolio data from load_portfolio()
    
    Returns:
        float: Total portfolio value in USD
    """
    stablecoins = {'USDT', 'USDC', 'DAI', 'TUSD', 'FDUSD', 'USDP', 'USDE', 'USD1', 'BFUSD', 'XUSD'}
    total_value = 0.0
    
    balances = portfolio.get("balances", [])
    
    for balance in balances:
        asset = balance.get("asset", "")
        free_amount = float(balance.get("free", 0.0))
        
        # Add stablecoin values directly (1:1)
        if asset in stablecoins:
            total_value += free_amount
        # For BTC, ETH, and other major assets, you could integrate price feeds here
        # For now, we'll only count stablecoins to get a conservative estimate
    
    return total_value


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
    print(f"loaded portfolio {portfolio}")
    total_portfolio_value_usd = calculate_portfolio_value(portfolio)

    position_size_percent = (quantity * entry_price / float(total_portfolio_value_usd) * 100) if total_portfolio_value_usd else 0.0

    trade = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
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
    }

    trade_json = json.dumps(trade, separators=(',', ':'), sort_keys=False)

    return trade_json
