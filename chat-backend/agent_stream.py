from typing import AsyncGenerator
from agent import get_agent

async def stream_agent_reply(session_id: str, user_input: str) -> AsyncGenerator[str, None]:
    # Get the agent instance for this specific session
    agent = get_agent(session_id)
    
    # Load tools if not already loaded
    if not hasattr(agent, '_tools_loaded'):
        await agent.load_tools()
        agent._tools_loaded = True
    
    async for item in agent.run(user_input):
        if hasattr(item, "choices"):
            for choice in item.choices:
                delta = choice.delta
                if delta and delta.content:
                    yield delta.content