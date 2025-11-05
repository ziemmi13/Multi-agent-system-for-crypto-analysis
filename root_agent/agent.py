from google.adk.agents import LlmAgent

from . import prompt

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Oversees business and technical cryptocurrencies analysts.',
    instruction=prompt.ROOT_AGENT_PROMPT,
    tools=[
        ],
)
