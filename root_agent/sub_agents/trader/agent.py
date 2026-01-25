from google.adk.agents import LlmAgent 

from .tools.trade import log_trade, process_trade_request
from .tools.portfolio_manager import load_portfolio, make_trade
from .prompt import TRADER_PROMPT

trader = LlmAgent(
    model='gemini-2.5-flash',
    name='trader',
    description='A crypto trader agent that simulates trading decisions based on the given instructions.',
    instruction=TRADER_PROMPT,
    tools=[make_trade, log_trade, process_trade_request, load_portfolio]
)