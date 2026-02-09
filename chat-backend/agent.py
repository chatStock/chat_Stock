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
        if len(s) > max_len:
            return s[:max_len] + "...(truncated)"
        return s
    except Exception as e:
        return f"<repr-failed {type(e).__name__}: {e}>"


def _dump_available_tools(agent: Agent, label: str):
    """
    HF MCP Agent doesn't expose `agent.tools`.
    It *does* expose `available_tools` (per your dir(agent)).
    This dump tells us what the agent thinks is callable right now.
    """
    try:
        at = getattr(agent, "available_tools", None)
        print(f"[DIAG] available_tools attr ({label}) = {type(at)}", file=sys.stderr, flush=True)

        # Some libs implement available_tools as a property returning dict/list
        # Others implement it as a method you call.
        if callable(at):
            tools_val = at()
            print(f"[DIAG] available_tools() ({label}) -> {type(tools_val)} = {_safe_repr(tools_val)}",
                  file=sys.stderr, flush=True)
        else:
            print(f"[DIAG] available_tools ({label}) -> {_safe_repr(at)}", file=sys.stderr, flush=True)

    except Exception as e:
        print(f"[DIAG] available_tools dump failed ({label}): {type(e).__name__}: {e}",
              file=sys.stderr, flush=True)


async def get_agent(session_id: str) -> Agent:
    """Get or create an agent for the session. Agents are cached per session."""

    _agent_request_counts[session_id] = _agent_request_counts.get(session_id, 0) + 1
    request_num = _agent_request_counts[session_id]

    if session_id not in _agents:
        print(f"\n{'='*80}", file=sys.stderr, flush=True)
        print(f"[AGENT] 🆕 Creating NEW agent for session: {session_id}", file=sys.stderr, flush=True)
        print(f"[AGENT] Request #: {request_num}", file=sys.stderr, flush=True)
        print(f"[AGENT] System prompt length: {len(SYSTEM_PROMPT)} chars", file=sys.stderr, flush=True)
        print(f"[AGENT] MCP server dir: {MCP_SERVER_DIR}", file=sys.stderr, flush=True)

        agent = Agent(
            model="Qwen/Qwen2.5-7B-Instruct",
            prompt=SYSTEM_PROMPT,
            servers=[
                {
                    "type": "stdio",
                    "command": sys.executable,
                    "args": ["-m", "app.server"],
                    "cwd": str(MCP_SERVER_DIR),
                    "env": {
                        "PYTHONPATH": str(MCP_SERVER_DIR),
                        "MARKET_API_URL": os.getenv("MARKET_API_URL", "http://market-api:9000"),
                    },
                }
            ],
        )

        # Keep your old diagnostics (even though tools attr doesn't exist for this class)
        print(f"[AGENT] Loading tools...", file=sys.stderr, flush=True)
        await agent.load_tools()
        _tools_loaded[session_id] = True

        if hasattr(agent, "tools"):
            print(f"[AGENT] ✓ Loaded {len(agent.tools)} tools:", file=sys.stderr, flush=True)
            for tool_name in agent.tools.keys():
                print(f"[AGENT]   - {tool_name}", file=sys.stderr, flush=True)
        else:
            print(f"[AGENT] ⚠️  Agent has no 'tools' attribute after load_tools()", file=sys.stderr, flush=True)

        # NEW: correct diagnostics for this HF MCP Agent
        _dump_available_tools(agent, "after first load_tools()")

        print(f"[AGENT] Agent type: {type(agent)}", file=sys.stderr, flush=True)
        print(f"[AGENT] Agent ID: {id(agent)}", file=sys.stderr, flush=True)

        _agents[session_id] = agent
        print(f"[AGENT] ✓ Agent cached for session {session_id}", file=sys.stderr, flush=True)
        print(f"{'='*80}\n", file=sys.stderr, flush=True)

    else:
        agent = _agents[session_id]
        print(f"\n{'='*80}", file=sys.stderr, flush=True)
        print(f"[AGENT] ♻️  REUSING cached agent for session: {session_id}", file=sys.stderr, flush=True)
        print(f"[AGENT] Request #: {request_num}", file=sys.stderr, flush=True)
        print(f"[AGENT] Agent ID: {id(agent)}", file=sys.stderr, flush=True)

        # Keep your old diagnostics
        if hasattr(agent, "tools"):
            print(f"[AGENT] Tools before reload: {len(agent.tools)}", file=sys.stderr, flush=True)
        else:
            print(f"[AGENT] ⚠️  WARNING: Cached agent has no tools attribute BEFORE reload!", file=sys.stderr, flush=True)

        # ✅ FIX: DO NOT reload tools on every request.
        # Reloading spawns a new MCP stdio server and causes duplicate-tool collisions:
        # "Tool already defined by another server. Skipping."
        loaded = _tools_loaded.get(session_id, False)
        print(f"[AGENT] Tools previously loaded for session? {loaded}", file=sys.stderr, flush=True)
        if not loaded:
            print(f"[AGENT] 🔄 Tools not marked loaded; calling load_tools() once.", file=sys.stderr, flush=True)
            await agent.load_tools()
            _tools_loaded[session_id] = True
        else:
            print(f"[AGENT] ✅ Skipping tool reload (prevents duplicate MCP server + tool collisions).",
                  file=sys.stderr, flush=True)

        # NEW: correct diagnostics
        _dump_available_tools(agent, "on reuse (no reload)")

        if hasattr(agent, "chat_history"):
            try:
                print(f"[AGENT] Chat history: {len(agent.chat_history)} messages", file=sys.stderr, flush=True)
            except Exception:
                pass

        print(f"{'='*80}\n", file=sys.stderr, flush=True)

    return _agents[session_id]
