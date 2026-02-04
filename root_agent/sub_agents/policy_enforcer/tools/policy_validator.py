from root_agent.sub_agents.trader.tools.portfolio_manager import load_portfolio
from .policy_loading import load_policy
import os

def validate_policy(transaction_data: dict) -> dict:
    """
    Validate the risk of a transaction based on provided risk management data.

    Parameters:
    transaction_data (dict): A dictionary containing transaction details.

    Returns:
        dict: A dictionary with validation results, including status and reasons.
    """

    # In case of HOLD, skip risk validation
    if transaction_data["action"].lower() == "hold":
        return {"status": "approved", "reason": "Hold action requires no risk validation."}
    
    policy_type = os.getenv("TRADING_STRATEGY", "aggressive")  # Default to aggressive
    policy = load_policy(policy_type=policy_type)
    portfolio_assets, full_portfolio_value_usd  = load_portfolio()

    # Unpack necessary data from policy
    max_position_size_percent = policy["risk_management"]["position_sizing"]["max_position_size_percent"]
    max_trades_per_day = policy["risk_management"]["daily_limits"]["max_trades_per_day"]
    whitelisted_assets = policy["asset_policies"]["whitelist"]["assets"]

    # Unpack transaction details
    action = transaction_data.get("action", "").lower()
    current_price = transaction_data.get("asset", {}).get("current_price_usd", 0.0)
    coin_symbol = transaction_data.get("asset", {}).get("symbol", "").lower()
    quantity = transaction_data.get("position", {}).get("quantity", 0.0)
    position_size_percent = transaction_data.get("position", {}).get("position_size_percent", 0.0)
    entry_price = transaction_data.get("position", {}).get("entry_price", None)
    target_exit_price = transaction_data.get("position", {}).get("target_exit_price", None)
    stop_loss_price = transaction_data.get("position", {}).get("stop_loss_price", None)
    order_type = transaction_data.get("position", {}).get("order_type", "").lower()
    coin_market_cap = transaction_data.get("asset", {}).get("coin_market_cap", 0.0)
    today_trade_count = transaction_data.get("today_trade_count", 0)

    ## Risk management Validations ##
    # Validation 1: Check if position size exceeds policy maximum
    if position_size_percent > max_position_size_percent:
        return {
            "status": "rejected",
            "reason": f"Position size {position_size_percent}% exceeds max allowed {max_position_size_percent}%",
            "field": "position_size_percent",
            "actual": position_size_percent,
            "limit": max_position_size_percent
        }
    
    # Validation 2: Daily limits
    if today_trade_count >= max_trades_per_day:
        return {
            "status": "rejected",
            "reason": f"Daily trade limit exceeded: {today_trade_count} trades today, max allowed {max_trades_per_day}",
            "field": "today_trade_count",
            "actual": today_trade_count,
            "limit": max_trades_per_day
        }

    # Validation 3: Stop loss
    if policy["risk_management"]["stop_loss"]["required"]:
        if stop_loss_price is None or stop_loss_price == 0:
            return {
                "status": "rejected",
                "reason": f"Stop-loss is required by policy but not set",
                "field": "stop_loss_price",
                "actual": stop_loss_price
            }
    
    # Validation 4: Take profit
    if policy["risk_management"]["take_profit"]["required"]:
        if target_exit_price is None or target_exit_price == 0:
            return {
                "status": "rejected",
                "reason": f"Take-profit is required by policy but not set",
                "field": "target_exit_price",
                "actual": target_exit_price
            }

    ## Asset policies Validations ##
    
    # Validation 1: Check if asset is whitelisted
    if policy["asset_policies"]["whitelist"]:
        if coin_symbol.upper() not in [a.upper() for a in whitelisted_assets]:
            return {
                "status": "rejected",
                "reason": f"Asset {coin_symbol.upper()} is not in whitelist. Allowed: {whitelisted_assets}",
                "field": "asset_symbol",
                "actual": coin_symbol.upper(),
                "allowed": whitelisted_assets
            }

    # Validation 2: Minimum market cap
    min_market_cap_usd = policy["asset_policies"]["minimum_market_cap_usd"]
    if coin_market_cap < min_market_cap_usd:
        return {
            "status": "rejected",
            "reason": f"Asset market cap ${coin_market_cap} is below minimum required ${min_market_cap_usd}",
            "field": "coin_market_cap",
            "actual": coin_market_cap,
            "limit": min_market_cap_usd
        }
        
    ## Trading rules Validations ##

    # Validation 1: Check if order type is allowed
    allowed_order_types = policy["trading_rules"]["allowed_order_types"]    
    if order_type not in [ot.lower() for ot in allowed_order_types]:
        return {
            "status": "rejected",
            "reason": f"Order type '{order_type}' is not allowed. Allowed types: {allowed_order_types}",
            "field": "order_type",
            "actual": order_type,
            "allowed": allowed_order_types
        }

    # Validation 2: Volatility check
    volatility_halt_threshold = policy["trading_rules"]["trading_halted_if_volatility_percent"] 
    volatility_1d = transaction_data.get("asset", {}).get("volatility_1d", 0.0)
    if volatility_1d > volatility_halt_threshold:
        return {
            "status": "rejected",
            "reason": f"Trading halted due to high volatility {volatility_1d:.2%} exceeding threshold {volatility_halt_threshold:.2%}",
            "field": "volatility_1d",
            "actual": volatility_1d,
            "limit": volatility_halt_threshold
        }

    # Validation 3: Liquidity check - skipped for now

        
    # If all validations pass
    return {
        "status": "approved",
        "reason": "All risk validations passed",
        "checked_validations": [
            "position_size",
            "daily_limits",
            "asset_whitelist",
            "stop_loss_requirement",
            "volatility_check"
        ]
    }

    