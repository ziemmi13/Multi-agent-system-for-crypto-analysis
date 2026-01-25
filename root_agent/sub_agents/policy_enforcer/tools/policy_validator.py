from .policy_loading import load_policy

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
    
    policy = load_policy(policy_type="aggressive")

    # Unpack necessary data from policy
    max_position_size_percent = policy["risk_management"]["position_sizing"]["max_position_size_percent"]
    max_single_asset_exposure_percent = policy["risk_management"]["position_sizing"]["max_single_asset_exposure_percent"]
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

    # Validation 1: Check if position size exceeds policy maximum
    if position_size_percent > max_position_size_percent:
        return {
            "status": "rejected",
            "reason": f"Position size {position_size_percent}% exceeds max allowed {max_position_size_percent}%",
            "field": "position_size_percent",
            "actual": position_size_percent,
            "limit": max_position_size_percent
        }
    
    # Validation 2: Check if asset is whitelisted
    if policy["asset_policies"]["whitelist"]:
        if coin_symbol.upper() not in [a.upper() for a in whitelisted_assets]:
            return {
                "status": "rejected",
                "reason": f"Asset {coin_symbol.upper()} is not in whitelist. Allowed: {whitelisted_assets}",
                "field": "asset_symbol",
                "actual": coin_symbol.upper(),
                "allowed": whitelisted_assets
            }
    
    # Validation 3: Check if stop-loss is set when required
    if policy["risk_management"]["stop_loss"]["required"]:
        if stop_loss_price is None or stop_loss_price == 0:
            return {
                "status": "rejected",
                "reason": f"Stop-loss is required by policy but not set",
                "field": "stop_loss_price",
                "actual": stop_loss_price
            }
        
    # If all validations pass
    return {
        "status": "approved",
        "reason": "All risk validations passed",
        "checked_validations": [
            "position_size",
            "asset_whitelist",
            "stop_loss_requirement"
        ]
    }

    