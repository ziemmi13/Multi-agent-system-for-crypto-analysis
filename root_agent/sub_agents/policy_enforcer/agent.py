from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import POLICY_ENFORCER_PROMPT
from .tools.policy_validator import validate_policy

policy_enforcer = LlmAgent(
    model='gemini-2.5-flash',
    name='policy_enforcer',
    description='A policy enforcer that ensures all actions comply with regulatory guidelines.',
    static_instruction=types.Content(role="system", parts=[types.Part(text=POLICY_ENFORCER_PROMPT)]),
    tools=[validate_policy],
    
)
