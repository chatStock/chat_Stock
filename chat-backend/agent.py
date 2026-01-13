import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import Agent

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MCP_SERVER_DIR = BASE_DIR / "mcp-server"

SYSTEM_PROMPT = """
You are a stock market assistant.

You have access to EXACTLY TWO tools:

1. get_news(symbol: str)
2. get_quote(symbol: str)

RULES:
- NEVER invent tool names
- ALWAYS call the correct tool
- If a tool fails, say data is unavailable
- NEVER hallucinate facts
"""

agent = Agent(
    model="Qwen/Qwen2.5-7B-Instruct",
    prompt=SYSTEM_PROMPT,
    servers=[
        {
            "type": "stdio",
            "command": sys.executable,
            "args": ["-m", "app.server"],
            "cwd": str(MCP_SERVER_DIR),  # ← REQUIRED
        }
    ],
)

async def ainput(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


async def chat_loop():
    while True:
        user_input = await ainput("You> ")
        if user_input.lower() in {"exit", "quit"}:
            break

        assistant_text = ""
        saw_tool_call = False
        saw_tool_response = False

        async for item in agent.run(user_input):

            if hasattr(item, "choices"):
                for choice in item.choices:
                    delta = choice.delta

                    if delta and delta.content:
                        assistant_text += delta.content

                    if delta and delta.tool_calls:
                        saw_tool_call = True
                        print("🛠️ TOOL CALL REQUEST:", delta.tool_calls)

            if isinstance(item, dict) and item.get("role") == "tool":
                saw_tool_response = True
                print("📦 TOOL RESPONSE:", item)

        if assistant_text.strip():
            print("Bot>", assistant_text.strip())
        else:
            print("Bot> (no assistant output)")

        if saw_tool_call and not saw_tool_response:
            print("⚠️ Tool was requested but no response was received.")
        elif saw_tool_response:
            print("✅ Tool call completed successfully.")


async def main():
    await agent.load_tools()
    print("✅ MCP tools loaded")
    await chat_loop()


if __name__ == "__main__":
    asyncio.run(main())