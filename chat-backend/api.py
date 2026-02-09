import sys
import os
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
"""

_agents = {}
_agent_request_counts = {}
_tools_loaded = {}  # session_id -> bool


def _safe_repr(obj, max_len=800):
    try:
        s = repr(obj)
        return s if len(s) <= max_len else s[:max_len] + "...(truncated)"
    except Exception as e:
        return f"<repr-failed {type(e).__name__}: {e}>"


def _dump_available_tools(agent: Agent, label: str):
    try:
        at = getattr(agent, "available_tools", None)
        print(f"[DIAG] available_tools attr ({label}) = {type(at)}",
              file=sys.stderr, flush=True)

        if callable(at):
            tools_val = at()
            print(f"[DIAG] available_tools() ({label}) -> {_safe_repr(tools_val)}",
                  file=sys.stderr, flush=True)
        else:
            print(f"[DIAG] available_tools ({label}) -> {_safe_repr(at)}",
                  file=sys.stderr, flush=True)

    except Exception as e:
        print(f"[DIAG] available_tools dump failed ({label}): {e}",
              file=sys.stderr, flush=True)


async def get_agent(session_id: str) -> Agent:
    _agent_request_counts[session_id] = _agent_request_counts.get(session_id, 0) + 1
    request_num = _agent_request_counts[session_id]

    if session_id not in _agents:
        print("\n" + "=" * 80, file=sys.stderr, flush=True)
        print(f"[AGENT] 🆕 Creating agent | session={session_id}", file=sys.stderr, flush=True)
        print(f"[AGENT] Request #: {request_num}", file=sys.stderr, flush=True)
        print(f"[AGENT] MCP_SERVER_DIR: {MCP_SERVER_DIR}", file=sys.stderr, flush=True)

        # 🔥 HARD FAIL if MCP dir is missing
        if not MCP_SERVER_DIR.exists():
            raise RuntimeError(f"MCP_SERVER_DIR does not exist: {MCP_SERVER_DIR}")

        agent = Agent(
            model="Qwen/Qwen2.5-7B-Instruct",
            prompt=SYSTEM_PROMPT,
            servers=[{
                "type": "stdio",
                "command": sys.executable,
                "args": ["-m", "app.server"],
                "cwd": str(MCP_SERVER_DIR),
                "env": {
                    "PYTHONPATH": str(MCP_SERVER_DIR),
                    "MARKET_API_URL": os.getenv("MARKET_API_URL", "http://market-api:9000"),
                },
            }],
        )

        print("[AGENT] Loading tools…", file=sys.stderr, flush=True)
        await agent.load_tools()
        _tools_loaded[session_id] = True

        _dump_available_tools(agent, "after load_tools()")

        _agents[session_id] = agent
        print(f"[AGENT] ✓ Agent cached | id={id(agent)}", file=sys.stderr, flush=True)
        print("=" * 80 + "\n", file=sys.stderr, flush=True)

    else:
        agent = _agents[session_id]
        print("\n" + "=" * 80, file=sys.stderr, flush=True)
        print(f"[AGENT] ♻️ Reusing agent | session={session_id}", file=sys.stderr, flush=True)
        print(f"[AGENT] Request #: {request_num}", file=sys.stderr, flush=True)

        if not _tools_loaded.get(session_id, False):
            print("[AGENT] ⚠ Tools not loaded yet — loading now", file=sys.stderr, flush=True)
            await agent.load_tools()
            _tools_loaded[session_id] = True
        else:
            print("[AGENT] ✅ Tools already loaded — skipping reload",
                  file=sys.stderr, flush=True)

        _dump_available_tools(agent, "reuse")

        print("=" * 80 + "\n", file=sys.stderr, flush=True)

    return _agents[session_id]
