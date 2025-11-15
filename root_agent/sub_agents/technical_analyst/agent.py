from google.adk.agents import LlmAgent 

from .tools.get_crypto_technical_data import get_crypto_technical_data
from .prompt import TECHNICAL_ANALYST_PROMPT

technical_analyst = LlmAgent(
    model='gemini-2.5-flash',
    name='technical_analyst',
    description='A crypto business analyst that analyses technical crypto data and prepares reports.',
    instruction=TECHNICAL_ANALYST_PROMPT,
    tools=[get_crypto_technical_data]
)
