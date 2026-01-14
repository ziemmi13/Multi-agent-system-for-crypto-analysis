import requests
from datetime import datetime, UTC
import os
import json

COINGECKO_ENDPOINT = "https://api.coingecko.com/api/v3"

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
        return data.get(coin_id, {}).get(currency)
    except:
        return None

def make_a_trade(action: str, coin_id: str, symbol: str,  currency: str = "usd"):
    """Execute or record a trading instruction.
    Returns a dict with a summary or an error message.
    """
    action_l = action.lower() if isinstance(action, str) else ""
    if action_l not in ("buy", "sell", "hold"):
        return {"error": "Unsupported action. Use 'buy', 'sell', or 'hold'."}

    price = get_current_price(coin_id, currency)

    log_trade(coin_id, symbol, price if price is not None else 0.0, currency, action_l)
    return {"action": action_l, "coin": coin_id, "symbol": symbol, "price": price if price is not None else 0.0}

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
    log_entry = f"{datetime.now(UTC).isoformat().replace("+00:00", "Z")} - {action.upper()} - {coin_id} ({symbol}) at {price_str} {currency}\n"
    log_file_path = os.path.join(os.path.dirname(__file__), "trade_log.txt")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)


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
    
    log_file_path = os.path.join(os.path.dirname(__file__), "trade_log.txt")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
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
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(rejection_entry, default=str) + "\n")
    
    return {"status": "logged", "message": f"Policy rejection logged for {symbol}"}


def process_trade_request(trade_request: dict) -> dict:
    """Process a structured TradeRequest (dict).

    Accepts either a dict following the TradeRequest contract or a JSON string.
    Executes or logs the trade using existing helpers and appends the full request
    and execution result to `trade_log.txt` for auditing.
    Returns a dict: {"trade_request": {...}, "execution": {...}} or an error dict.
    """
    # Expect a dict (the agent runtime will pass parsed JSON as a dict).
    if not isinstance(trade_request, dict):
        return {"error": "trade_request must be a dict"}

    # Basic validation
    action = trade_request.get("action", "").lower()
    asset = trade_request.get("asset", {})
    position = trade_request.get("position", {})

    coin_id = asset.get("coin_id")
    symbol = asset.get("symbol")
    currency = asset.get("currency", "usd")

    if action not in ("buy", "sell", "hold"):
        return {"error": "Invalid action in trade_request"}
    if not coin_id or not symbol:
        return {"error": "asset.coin_id and asset.symbol are required"}

    execution = None
    try:
        if action == "hold":
            # Use make_a_trade to fetch price & log hold
            exec_res = make_a_trade("hold", coin_id, symbol, currency)
            execution = {"status": "logged_hold", "result": exec_res}
        else:
            exec_res = make_a_trade(action, coin_id, symbol, currency)
            if exec_res.get("error"):
                execution = {"status": "error", "result": exec_res}
            else:
                execution = {"status": "executed", "result": exec_res}
    except Exception as e:
        execution = {"status": "error", "result": str(e)}

    # Append audit log with the full request and execution result
    try:
        log_file_path = os.path.join(os.path.dirname(__file__), "trade_log.txt")
        with open(log_file_path, "a", encoding="utf-8") as f:
            entry = {"timestamp": datetime.utcnow().isoformat(), "trade_request": trade_request, "execution": execution}
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass

    return {"trade_request": trade_request, "execution": execution}


def process_trade_request_json(trade_request_json: str) -> dict:
    """Wrapper that accepts a JSON string, parses it, and calls `process_trade_request`.

    Useful for tool APIs that prefer a single-string parameter.
    """
    try:
        payload = json.loads(trade_request_json)
    except Exception as e:
        return {"error": f"Invalid JSON: {e}"}

    return process_trade_request(payload)
    