from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from google.genai import types
import logging
import os
import pathlib
import sys  # Potrzebne do przekierowania na stdout

from . import prompt
from .tools.trade_request_formatter import format_trade_request

from .sub_agents.business_analyst_1.agent import business_analyst_1
from .sub_agents.business_analyst_2.agent import business_analyst_2
from .sub_agents.technical_analyst.agent import technical_analyst
from .sub_agents.policy_enforcer.agent import policy_enforcer
from .sub_agents.trader.agent import trader
from .sub_agents.trader.tools.trade import get_trade_history, log_policy_rejection

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Konfiguracja bazowa
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables 
root_dir = pathlib.Path(__file__).parent
load_dotenv(root_dir / '.env')

# Config
my_config = GenerateContentConfig(
    temperature=0.5,
    top_k=50,
    top_p=0.9,
    presence_penalty=0.0,
    frequency_penalty=0.0,
    candidate_count=1,
)

# Choose prompt based on strategy
strategy = os.getenv("TRADING_STRATEGY")
if strategy == "safe":
    selected_prompt = prompt.ROOT_AGENT_PROMPT_SAFE
else:
    selected_prompt = prompt.ROOT_AGENT_PROMPT_AGGRESSIVE

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Oversees business and technical cryptocurrencies analysts.',
    static_instruction=types.Content(role="system", parts=[types.Part(text=selected_prompt)]),
    tools=[
        AgentTool(agent=business_analyst_1),
        AgentTool(agent=business_analyst_2),
        AgentTool(agent=technical_analyst),
        AgentTool(agent=policy_enforcer),
        AgentTool(agent=trader),
        format_trade_request,
        log_policy_rejection,
        get_trade_history,
    ],
    generate_content_config=my_config,
)