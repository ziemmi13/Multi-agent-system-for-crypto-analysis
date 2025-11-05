from google.adk.agents import LlmAgent

from . import prompt

from .tools.cryptopanic_news_tool import get_news_from_cryptopanic
business_analyst_2 = LlmAgent(
    model='gemini-2.5-flash',
    name='business_analyst_2',
    description='A crypto business analyst that analyses news articles and prepares business reports.',
    instruction=prompt.BUSINESS_ANALYST_PROMPT2,
    tools=[get_news_from_cryptopanic]
)
