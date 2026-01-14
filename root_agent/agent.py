from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.business_analyst_1.agent import business_analyst_1
from .sub_agents.business_analyst_2.agent import business_analyst_2
from .sub_agents.technical_analyst.agent import technical_analyst
from .sub_agents.policy_enforcer.agent import policy_enforcer
from .sub_agents.trader.agent import trader
from .tools.trade_formatter import format_trade_request

root_agent = LlmAgent(
    model='gemini-2.5-flash',
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
        ],
)
