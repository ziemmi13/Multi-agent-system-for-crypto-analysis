import json

def load_portfolio(portfolio_path: str = "portfolio/portfolio.json") -> dict:
    """Load the current portfolio from a JSON file."""

    with open(portfolio_path, 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    return portfolio
