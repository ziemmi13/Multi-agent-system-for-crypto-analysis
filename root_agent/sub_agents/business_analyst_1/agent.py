from google.adk.agents import LlmAgent
from . import prompt
from google.adk.tools.agent_tool import AgentTool
from .tools.rag_tool import search_similar_news
from .tools.cryptopanic_news_tool import get_news_from_cryptopanic
from google.genai import types
from google.adk.tools.function_tool import FunctionTool
from .sub_agents.google_search_agent.agent import google_search_agent

business_analyst_1 = LlmAgent(
    model='gemini-2.5-flash',
    name='business_analyst_1',
    description='A crypto business analyst that analyses news articles and prepares business reports.',
    static_instruction=types.Content(role="system", parts=[types.Part(text=prompt.BUSINESS_ANALYST_PROMPT1)]),
    tools=[
        get_news_from_cryptopanic,
        search_similar_news,
        AgentTool(agent=google_search_agent)
    ],
    sub_agents=[google_search_agent]
)
