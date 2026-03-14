"""Root agent definition for postable-ia.

The agent is wired up with Google ADK and exposed via `adk api_server` or
`adk web` for local development.
"""

from google.adk.agents import Agent

from . import tools

root_agent = Agent(
    # Model — change to any Gemini model you have access to.
    model="gemini-2.0-flash",
    name="postable_ia",
    description="Postable AI agent powered by Google ADK.",
    instruction=(
        "You are a helpful AI assistant for Postable. "
        "Answer questions accurately and concisely."
    ),
    tools=[
        tools.example_tool,
    ],
)
