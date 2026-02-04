import json
import os

def load_policy(policy_type) -> dict:
    """Load a policy JSON file from the tools directory."""
    tools_dir = os.path.dirname(__file__)
    policy_path = os.path.join(tools_dir, f"policy_{policy_type}.json")
    
    with open(policy_path, 'r') as f:
        policy_dict = json.load(f)
    
    return policy_dict