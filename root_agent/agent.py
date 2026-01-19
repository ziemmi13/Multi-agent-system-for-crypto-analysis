from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
# for external LLM providers
from google.adk.models.lite_llm import LiteLlm

from . import prompt
from .sub_agents.business_analyst_1.agent import business_analyst_1
from .sub_agents.business_analyst_2.agent import business_analyst_2
from .sub_agents.technical_analyst.agent import technical_analyst
from .sub_agents.policy_enforcer.agent import policy_enforcer
from .sub_agents.trader.agent import trader
from .sub_agents.trader.tools.trade import log_policy_rejection
from .tools.trade_formatter import format_trade_request
from dotenv import load_dotenv
import pathlib
import os
import tiktoken

# Load environment variables 
root_dir = pathlib.Path(__file__).parent
load_dotenv(root_dir / '.env')

# Encoding
encoding = tiktoken.encoding_for_model('gpt-4.1')

# Models
gemini_model = 'gemini-2.5-flash'
open_ai_model = LiteLlm(model='openai/gpt-4.1',
                  api_key=os.getenv("OPENAI_API_KEY"),
                  logit_bias={
                          encoding.encode("buy")[0]: 5,
                          encoding.encode("sell")[0]: 5,
                          encoding.encode("hold")[0]: -10,
                    }  
                  )

root_agent = LlmAgent(
    model=gemini_model,
    name='root_agent',
    description='Oversees business and technical cryptocurrencies analysts.',
    instruction=prompt.ROOT_AGENT_PROMPT,
    tools=[
        AgentTool(agent=business_analyst_1), 
        AgentTool(agent=business_analyst_2),
        AgentTool(agent=technical_analyst),
        AgentTool(agent=policy_enforcer),
        AgentTool(agent=trader),
        format_trade_request,
        log_policy_rejection,
        ],
)
