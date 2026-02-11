from ...trader.tools.portfolio_manager import load_portfolio
from .policy_loading import load_policy
import logging
import os

logger = logging.getLogger("root_agent")

def validate_policy(transaction_data: dict) -> dict:
    """
    Validate the risk of a transaction based on provided risk management data.

    Parameters:
    transaction_data (dict): A dictionary containing transaction details.

    Returns:
        dict: A dictionary with validation results, including status and reasons.
    """

    logger.info("Starting policy validation")

    # Basic action validation
    action_raw = transaction_data.get("action")
    if not isinstance(action_raw, str) or not action_raw:
        logger.error(
            "Policy validation rejected: invalid or missing 'action' in transaction_data=%s",
            transaction_data,
        )
        return {
            "status": "rejected",
            "reason": "Invalid or missing 'action' field in transaction data.",
            "field": "action",
            "actual": action_raw,
        }

    # In case of HOLD, skip risk validation
    if action_raw.lower() == "hold":

        return {"status": "approved", "reason": "Hold action requires no risk validation."}
    
    policy_type = os.getenv("TRADING_STRATEGY", "aggressive")  # Default to aggressive
    policy = load_policy(policy_type=policy_type)
    portfolio_assets, full_portfolio_value_usd = load_portfolio()

    # Unpack necessary data from policy
    max_position_size_percent = policy["risk_management"]["position_sizing"]["max_position_size_percent"]
    max_trades_per_day = policy["risk_management"]["daily_limits"]["max_trades_per_day"]
    whitelisted_assets = policy["asset_policies"]["whitelist"]["assets"]

    # Unpack transaction details
    action = action_raw.lower()
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

    logger.info("Validating transaction: action=%s, symbol=%s, position_size_percent=%.4f, today_trade_count=%s, order_type=%s, coin_market_cap=%s, current_price=%s",
        action,
        coin_symbol.upper(),
        position_size_percent,
        today_trade_count,
        order_type,
        coin_market_cap,
        current_price,
    )

    ## Risk management Validations ##
    # Validation 1: Check if position size exceeds policy maximum
    if position_size_percent > max_position_size_percent:
        logger.warning(
            "Policy validation failed: position size too large. position_size_percent=%.4f, "
            "max_allowed=%.4f, action=%s, symbol=%s",
            position_size_percent,
            max_position_size_percent,
            action,
            coin_symbol.upper(),
        )
        return {
            "status": "rejected",
            "reason": f"Position size {position_size_percent}% exceeds max allowed {max_position_size_percent}%",
            "field": "position_size_percent",
            "actual": position_size_percent,
            "limit": max_position_size_percent
        }
    
    # Validation 2: Daily limits
    if today_trade_count >= max_trades_per_day:
        logger.warning(
            "Policy validation failed: daily trade limit exceeded. today_trade_count=%s, "
            "max_trades_per_day=%s, action=%s, symbol=%s",
            today_trade_count,
            max_trades_per_day,
            action,
            coin_symbol.upper(),
        )
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
            logger.warning(
                "Policy validation failed: stop-loss required but not set. action=%s, symbol=%s",
                action,
                coin_symbol.upper(),
            )
            return {
                "status": "rejected",
                "reason": f"Stop-loss is required by policy but not set",
                "field": "stop_loss_price",
                "actual": stop_loss_price
            }
    
    # Validation 4: Take profit
    if policy["risk_management"]["take_profit"]["required"]:
        if target_exit_price is None or target_exit_price == 0:
            logger.warning(
                "Policy validation failed: take-profit required but not set. action=%s, symbol=%s",
                action,
                coin_symbol.upper(),
            )
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
            logger.warning(
                "Policy validation failed: asset not in whitelist. symbol=%s, whitelist=%s",
                coin_symbol.upper(),
                whitelisted_assets,
            )
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
        logger.warning(
            "Policy validation failed: market cap below minimum. symbol=%s, coin_market_cap=%s, "
            "min_market_cap_usd=%s",
            coin_symbol.upper(),
            coin_market_cap,
            min_market_cap_usd,
        )
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
        logger.warning(
            "Policy validation failed: order type not allowed. order_type=%s, allowed_order_types=%s, "
            "action=%s, symbol=%s",
            order_type,
            allowed_order_types,
            action,
            coin_symbol.upper(),
        )
        return {
            "status": "rejected",
            "reason": f"Order type '{order_type}' is not allowed. Allowed types: {allowed_order_types}",
            "field": "order_type",
            "actual": order_type,
            "allowed": allowed_order_types
        }

    # Validation 2: Volatility check
    volatility_halt_threshold = policy["trading_rules"]["trading_halted_if_volatility_percent"] 
    volatility_1d_percent = transaction_data.get("asset", {}).get("volatility_1d", 0.0)
    if volatility_1d_percent > volatility_halt_threshold:
        logger.warning(
            "Policy validation failed: volatility too high. volatility_1d_percent=%s, "
            "volatility_halt_threshold=%s, symbol=%s",
            volatility_1d_percent,
            volatility_halt_threshold,
            coin_symbol.upper(),
        )
        return {
            "status": "rejected",
            "reason": f"Trading halted due to high volatility {volatility_1d_percent:.2%} exceeding threshold {volatility_halt_threshold:.2%}",
            "field": "volatility_1d",
            "actual": volatility_1d_percent,
            "limit": volatility_halt_threshold
        }

    # Validation 3: Liquidity check - skipped for now


    # If all validations pass
    approval_payload = {
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
    logger.info(
        "Policy validation approved. action=%s, symbol=%s, details=%s",
        action,
        coin_symbol.upper(),
        approval_payload,
    )
    return approval_payload

    