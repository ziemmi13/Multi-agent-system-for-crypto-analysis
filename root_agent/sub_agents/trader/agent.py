from google.adk.agents import LlmAgent 
from google.genai import types

from .tools.trade import log_trade, process_trade_request
from .tools.portfolio_manager import load_portfolio, make_trade
from .prompt import TRADER_PROMPT

trader = LlmAgent(
    model='gemini-2.5-flash',
    name='trader',
    description='A crypto trader agent that simulates trading decisions based on the given instructions.',
    static_instruction=types.Content(role="system", parts=[types.Part(text=TRADER_PROMPT)]),
    tools=[make_trade, log_trade, process_trade_request, load_portfolio]
)