from google.adk.agents import LlmAgent
from . import prompt
from google.adk.tools.google_search_tool import google_search
from google.genai import types

google_search_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='google_search_agent',
    description='A google search agent that can search the web for crypto related news.',
    static_instruction=types.Content(role="system", parts=[types.Part(text=prompt.GOOGLE_SEARCH_AGENT_PROMPT)]),
    tools=[google_search],
)
