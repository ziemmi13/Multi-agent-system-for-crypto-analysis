from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from . import prompt
from .tools.rag_tool import search_similar_news
from .tools.cryptopanic_news_tool import get_news_from_cryptopanic

business_analyst_1 = LlmAgent(
    model='gemini-2.5-flash',
    name='business_analyst_1',
    description='A crypto business analyst that analyses news articles and prepares business reports.',
    instruction=prompt.BUSINESS_ANALYST_PROMPT1,
    tools=[google_search, get_news_from_cryptopanic, search_similar_news]
)
