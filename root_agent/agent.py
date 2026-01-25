from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from google.genai import types
# for external LLM providers
from google.adk.models.lite_llm import LiteLlm


from . import prompt
from .sub_agents.business_analyst_1.agent import business_analyst_1
from .sub_agents.business_analyst_2.agent import business_analyst_2
from .sub_agents.technical_analyst.agent import technical_analyst
from .sub_agents.policy_enforcer.agent import policy_enforcer
from .sub_agents.trader.agent import trader
from .sub_agents.trader.tools.trade import log_policy_rejection
from .tools.trade_request_formatter import format_trade_request
from dotenv import load_dotenv
import pathlib
import os
import tiktoken

# Load environment variables 
root_dir = pathlib.Path(__file__).parent
load_dotenv(root_dir / '.env')

# Encoding
encoding = tiktoken.encoding_for_model('gpt-4.1')

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

gemini_model = 'gemini-2.5-flash'
open_ai_model = LiteLlm(model='openai/gpt-4.1',
                  api_key=os.getenv("OPENAI_API_KEY"),
                  logit_bias={
                          encoding.encode("buy")[0]: 5,
                          encoding.encode("sell")[0]: 5,
                          encoding.encode("hold")[0]: -10,
                    }  
                  ) # For now the openai model doesn't work with tools

root_agent = LlmAgent(
    model=gemini_model,
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
        ],
    generate_content_config=my_config,
)
