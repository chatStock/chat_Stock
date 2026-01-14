 
from typing import AsyncGenerator
from agent import get_agent

async def stream_agent_reply(session_id: str, user_input: str) -> AsyncGenerator[str, None]:
    """
    Stream a reply for ONE user message.

    We intentionally create a fresh Agent per request to avoid state/tool-call
    lockout issues caused by reusing a HuggingFace Agent instance across turns.
    """
    agent = get_agent()
    await agent.load_tools()

    async for item in agent.run(user_input):
        if hasattr(item, "choices"):
            for choice in item.choices:
                delta = choice.delta
                if delta and delta.content:
                    yield delta.content