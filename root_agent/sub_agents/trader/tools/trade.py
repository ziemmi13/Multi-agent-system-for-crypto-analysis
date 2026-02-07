from locale import currency
import logging
import requests
from datetime import datetime, UTC
import os
import json
from .portfolio_manager import make_trade

logger = logging.getLogger(__name__)

COINGECKO_ENDPOINT = "https://api.coingecko.com/api/v3"
TRADE_LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "trade_log.txt")

def get_current_price(coin_id: str, currency: str = "usd"):
    """Fetches the current price of a cryptocurrency from the CoinGecko API.
    Args:
        coin_id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin').
        currency (str, optional): The currency in which the price is denominated (e.g., 'usd').
    Returns:
        float: The current price of the cryptocurrency.
    """
    current_price_endpoint = f"{COINGECKO_ENDPOINT}/simple/price?ids={coin_id}&vs_currencies={currency}"
    try:
        response = requests.get(current_price_endpoint, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get(coin_id, {}).get(currency, None)
    except:
        return None

def log_trade(action: str, coin_id: str, symbol: str, current_price: float, currency: str = "usd"):
    """Logs the trade action to a local file with a timestamp.
    Args:
        action (str): The trade action ('buy', 'sell', or 'hold').
        coin_id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin').
        symbol (str): The symbol of the cryptocurrency (e.g., 'btc').
        current_price (float): The current price of the cryptocurrency.
        currency (str): The currency in which the price is denominated.
        action (str): The trade action ('buy', 'sell', or 'hold').
    """
    action_l = action.lower() if isinstance(action, str) else ""
    if action_l not in ("buy", "sell", "hold"):
        return {"error": "Unsupported action. Use 'buy', 'sell', or 'hold'."}
    
    if current_price is None:
        price_str = str(get_current_price(coin_id, currency))
    else:
        price_str = str(current_price)

    log_entry = f"{datetime.now(UTC).isoformat().replace("+00:00", "Z")} - {action.upper()} - {coin_id} ({symbol}) at {price_str} {currency}\n"
    with open(TRADE_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
    logger.info(log_entry)
    return {"status": "logged", "message": f"Trade action '{action}' for {symbol} logged at price {price_str} {currency}."}


def log_policy_rejection(trade_request: dict, rejection_reason: str, violations: list[dict], policy_response: dict):
    """Logs a policy rejection to the trade log file.
    
    Args:
        trade_request (dict): The trade request that was rejected.
        rejection_reason (str, optional): The reason for rejection. If not provided, will extract from policy_response.
        violations (list, optional): List of policy violations.
        policy_response (dict, optional): The full policy_enforcer response dict. If provided, will extract reason and violations.
    """
    # Extract rejection reason from policy_response if provided
    if policy_response and not rejection_reason:
        rejection_reason = policy_response.get("reason", "Policy violation")
        # Build violations list from policy_response fields
        if not violations:
            violations = []
            if "field" in policy_response:
                violations.append({
                    "field": policy_response.get("field"),
                    "actual": policy_response.get("actual"),
                    "limit": policy_response.get("limit"),
                    "allowed": policy_response.get("allowed")
                })
    
    asset = trade_request.get("asset", {})
    symbol = asset.get("symbol", "unknown")
    coin_id = asset.get("coin_id", "unknown")
    action = trade_request.get("action", "unknown").upper()
    currency = asset.get("currency", "usd")
    current_price = asset.get("current_price_usd", 0.0)
    
    # Create rejection log entry
    reason_text = rejection_reason or "Policy violation"
    log_entry = f"{datetime.now(UTC).isoformat().replace("+00:00", "Z")} - REJECTED - {coin_id} ({symbol}) at {current_price} {currency} - Reason: {reason_text}\n"
    
    with open(TRADE_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
    
    # Also log the full JSON entry for audit trail
    rejection_entry = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "trade_request": trade_request,
        "policy_status": "REJECTED",
        "rejection_reason": reason_text,
        "violations": violations or [],
        "policy_response": policy_response
    }
    with open(TRADE_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(rejection_entry, default=str) + "\n")
    logger.warning(rejection_entry)
    return {"status": "logged", "message": f"Policy rejection logged for {symbol}"}


def process_trade_request(trade_request: dict) -> dict:
    """Process a structured TradeRequest (dict).

    Accepts a dict following the TradeRequest contract.
    For BUY/SELL: Calls make_trade() from portfolio_manager to execute on Binance,
                  then calls log_trade() if the trade actually executes.
    For HOLD:     Only logs the hold action without executing any trade.
    Appends the full request and execution result to `trade_log.txt` for auditing.
    Returns a dict: {"trade_request": {...}, "execution": {...}} or an error dict.
    """
    # Expect a dict (the agent runtime will pass parsed JSON as a dict).
    if not isinstance(trade_request, dict):
        logger.warning("process_trade_request rejected: trade_request must be a dict")
        return {"error": "trade_request must be a dict"}

    # Basic validation
    action = trade_request.get("action", "").lower()
    logger.info("Processing trade request: action=%s, asset=%s", action, trade_request.get("asset", {}).get("symbol", "?"))
    asset = trade_request.get("asset", {})
    position = trade_request.get("position", {})
    order_type = position.get("order_type", "MARKET").upper()
    entry_price = position.get("entry_price", 0.0)
    current_price = asset.get("current_price_usd", 0.0)

    coin_id = asset.get("coin_id")
    symbol = asset.get("symbol")
    currency = asset.get("currency", "usd")

    execution = None
    if action == "hold":
        log_res = log_trade(action, coin_id, symbol, current_price, currency)
        execution = {"status": "logged_hold", "result": log_res}
        logger.info("Hold logged for %s (%s)", symbol, coin_id)
    else: # BUY or SELL
        binance_symbol = f"{symbol.upper()}USDT"
        side = "BUY" if action == "buy" else "SELL"
        
        # Get quantity from position 
        quantity = position.get("quantity", 0.001)
        
        # Execute the trade using make_trade from portfolio_manager
        try:
            trade_result = make_trade(symbol=binance_symbol,
                                        side=side,
                                        quantity=quantity,
                                        order_type=order_type,
                                        price=entry_price,
                                        stop_price=position.get("stop_price", 0.0),
                                        time_in_force="GTC")
            
            # If trade executed successfully, log it
            if trade_result and not trade_result.get("error"):
                logger.info("Trade executed: %s %s (%s)", action.upper(), symbol, coin_id)
                log_res = log_trade(action, coin_id, symbol, current_price, currency)
                execution = {"status": "executed", "result": {"trade": trade_result, "log": log_res}}
                
            else:
                logger.error("Trade execution error: %s", trade_result)
                execution = {"status": "error", "result": trade_result}
        except Exception as e:
            execution = {"status": "error", "result": f"Trade execution failed: {str(e)}"}
            logger.exception("Trade execution failed for %s (%s)", symbol or "?", coin_id or "?")

    # Append audit log with the full request and execution result
    try:
        with open(TRADE_LOG_FILE_PATH, "a", encoding="utf-8") as f:
            entry = {"timestamp": datetime.now().isoformat(), "trade_request": trade_request, "execution": execution}
            f.write(json.dumps(entry, default=str) + "\n")
            logger.info("Audit log entry written: %s", entry)
    except Exception:
        logger.error("Failed to write audit log entry: %s", entry)

    return {"trade_request": trade_request, "execution": execution}


def get_trade_history(limit: int = 20) -> dict:
    """Gets the trade history from the trade log file.
    Args:
        limit (int, optional): The number of trades to return. Defaults to 20.
    Returns:
        dict: A dictionary containing the trade history and today's trade count.
    """
    
    today_trade_count = 0
    today = datetime.now(UTC).date()

    try:
        with open(TRADE_LOG_FILE_PATH, "r") as f:
            lines = f.readlines()
        
        reversed_lines = [line for line in reversed(lines)]
        
        trade_history = []
        for line in reversed_lines[:limit]:
            try:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry["timestamp"]).date()
                if entry_date == today:
                    # Check if it's a HOLD action
                    entry_str = str(entry).lower()
                    if "hold" in entry_str: 
                        pass
                    else:
                        today_trade_count += 1
                trade_history.append(entry)
            except:
                entry_date = datetime.fromisoformat(line.split(" - ")[0].replace("Z", "+00:00")).date()                    
                if entry_date == today:
                    entry_str = str(entry).lower()
                    if "hold" in entry_str: 
                        pass
                    else:
                        today_trade_count += 1
                trade_history.append(line)

    except Exception:
        return {"error": "Failed to get trade history", "trade_history": [], "today_trade_count": today_trade_count}
    
    return {"trade_history": trade_history, "today_trade_count": today_trade_count}
