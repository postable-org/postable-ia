"""Custom tool functions for the Postable agent.

Each plain Python function decorated with @tool (or just passed to Agent.tools)
becomes a callable tool the agent can invoke during a conversation.

ADK automatically generates the tool schema from the function signature and
docstring, so keep them descriptive.
"""


def example_tool(query: str) -> str:
    """A placeholder tool that echoes the query back.

    Replace this with real logic — e.g. a database lookup, an API call, or
    any computation the agent should be able to perform.

    Args:
        query: The input string to process.

    Returns:
        A string with the result.
    """
    return f"[example_tool] received: {query}"
