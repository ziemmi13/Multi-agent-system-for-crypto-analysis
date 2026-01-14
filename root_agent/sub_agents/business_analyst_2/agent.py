from google.adk.agents import LlmAgent 

from .tools.get_telegram_news import get_telegram_news
from .prompt import BUSINESS_ANALYST_2_PROMPT

business_analyst_2 = LlmAgent(
    model='gemini-2.5-flash',
    name='business_analyst_2',
    description='A business analyst that specializes in gathering and analyzing business news from Telegram channels.',
    instruction=BUSINESS_ANALYST_2_PROMPT,
    tools=[get_telegram_news]
)
