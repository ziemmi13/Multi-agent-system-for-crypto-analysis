from dotenv import load_dotenv
import pathlib
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from google.genai import types

from . import prompt
from .sub_agents.business_analyst_1.agent import business_analyst_1
from .sub_agents.business_analyst_2.agent import business_analyst_2
from .sub_agents.technical_analyst.agent import technical_analyst
from .sub_agents.policy_enforcer.agent import policy_enforcer
from .sub_agents.trader.agent import trader
from .sub_agents.trader.tools.trade import get_trade_history, log_policy_rejection
from .tools.trade_request_formatter import format_trade_request

# Load environment variables 
root_dir = pathlib.Path(__file__).parent
load_dotenv(root_dir / '.env')

# Generation config
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,       
    "max_output_tokens": 5000,
}

# Models
my_config = GenerateContentConfig(
    temperature=0,
    top_k=20,
    top_p=0.95,
    # max_output_tokens=1000,
    presence_penalty=0.0,
    frequency_penalty=0.0,
    # stop_sequences=["STOP!"],
    # response_mime_type="application/json", # This will cause an error if agent uses tools
    candidate_count=1,
)

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Oversees business and technical cryptocurrencies analysts.',
    static_instruction=types.Content(role="system", parts=[types.Part(text=prompt.ROOT_AGENT_PROMPT)]),
    # instruction="BTC",
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
