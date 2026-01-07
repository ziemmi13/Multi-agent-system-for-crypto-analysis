from google.adk.agents import LlmAgent 

from .tools.policy_validator import validate_policy
from .prompt import POLICY_ENFORCER_PROMPT

policy_enforcer = LlmAgent(
    model='gemini-2.5-flash',
    name='policy_enforcer',
    description='A policy enforcer that ensures all actions comply with regulatory guidelines.',
    instruction=POLICY_ENFORCER_PROMPT,
    tools=[validate_policy]
)
