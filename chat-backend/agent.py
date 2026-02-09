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

# -------------------------------------------------------------------
# Rolling memory (per session) — Idea #1
# -------------------------------------------------------------------
_session_summary = {}        # session_id -> str
_session_turns = {}          # session_id -> list[tuple[str,str]]  (user, assistant)

# Tuning knobs
KEEP_LAST_TURNS = 6          # how many recent turns we keep verbatim
SUMMARIZE_AFTER_TURNS = 12   # when turns exceed this, compress
MAX_PROMPT_CHARS = 14000     # crude safety bound (chars proxy for tokens)


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
            print(
                f"[DIAG] available_tools() ({label}) -> {type(tools_val)} = {_safe_repr(tools_val)}",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(f"[DIAG] available_tools ({label}) -> {_safe_repr(at)}", file=sys.stderr, flush=True)

    except Exception as e:
        print(
            f"[DIAG] available_tools dump failed ({label}): {type(e).__name__}: {e}",
            file=sys.stderr,
            flush=True,
        )


# -------------------------------------------------------------------
# Rolling memory helpers
# -------------------------------------------------------------------
def _get_turns(session_id: str):
    return _session_turns.setdefault(session_id, [])


def _get_summary(session_id: str) -> str:
    return _session_summary.get(session_id, "")


def record_turn(session_id: str, user: str, assistant: str) -> None:
    """
    Call this after you produce the final assistant response.
    """
    _get_turns(session_id).append((user, assistant))


def build_compact_prompt(session_id: str, user_input: str) -> str:
    """
    Returns a prompt that includes:
    - stable system prompt (your tool rules)
    - rolling summary memory
    - last N verbatim turns
    - current user message

    NOTE: You should pass THIS to agent.run(), and clear agent.chat_history.
    """
    summary = _get_summary(session_id).strip()
    turns = _get_turns(session_id)[-KEEP_LAST_TURNS:]

    parts = []
    parts.append(SYSTEM_PROMPT.strip() + "\n\n")
    parts.append("You are continuing an ongoing conversation.\n\n")

    if summary:
        parts.append("=== Conversation Summary (memory) ===\n")
        parts.append(summary + "\n\n")

    if turns:
        parts.append("=== Recent Turns ===\n")
        for u, a in turns:
            parts.append(f"User: {u}\nAssistant: {a}\n")
        parts.append("\n")

    parts.append("=== Current User Message ===\n")
    parts.append(user_input)

    prompt = "".join(parts)

    # crude clamp — prevents pathological growth even if summarization fails
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[-MAX_PROMPT_CHARS:]

    return prompt


async def maybe_summarize_session(agent: Agent, session_id: str) -> None:
    """
    If turns exceed SUMMARIZE_AFTER_TURNS, summarize older turns into _session_summary
    and keep only the last KEEP_LAST_TURNS verbatim.
    """
    turns = _get_turns(session_id)
    if len(turns) < SUMMARIZE_AFTER_TURNS:
        return

    # Summarize everything except the last KEEP_LAST_TURNS (keep those verbatim)
    to_summarize = turns[:-KEEP_LAST_TURNS]
    if not to_summarize:
        return

    prev_summary = _get_summary(session_id).strip()

    transcript_lines = []
    for u, a in to_summarize:
        transcript_lines.append(f"User: {u}\nAssistant: {a}\n")
    transcript = "\n".join(transcript_lines)

    summarizer_prompt = f"""
You are a summarizer. Do NOT call any tools.

Update (or create) a compact memory summary of the conversation so far.
Focus on:
- user intent / task
- decisions made
- constraints
- important facts/names
- unresolved issues
Keep it concise (max ~250-350 tokens).

Previous summary (if any):
{prev_summary if prev_summary else "(none)"}

Transcript to incorporate:
{transcript}

Return ONLY the updated summary text.
""".strip()

    # Prevent agent internal history from ballooning / interfering with summarization
    if hasattr(agent, "chat_history"):
        try:
            agent.chat_history = []
        except Exception:
            pass

    chunks = []
    async for item in agent.run(summarizer_prompt):
        if hasattr(item, "choices") and item.choices:
            for choice in item.choices:
                delta = getattr(choice, "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    chunks.append(content)

    new_summary = "".join(chunks).strip()
    if new_summary:
        _session_summary[session_id] = new_summary
        _session_turns[session_id] = turns[-KEEP_LAST_TURNS:]


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
        loaded = _tools_loaded.get(session_id, False)
        print(f"[AGENT] Tools previously loaded for session? {loaded}", file=sys.stderr, flush=True)
        if not loaded:
            print(f"[AGENT] 🔄 Tools not marked loaded; calling load_tools() once.", file=sys.stderr, flush=True)
            await agent.load_tools()
            _tools_loaded[session_id] = True
        else:
            print(
                f"[AGENT] ✅ Skipping tool reload (prevents duplicate MCP server + tool collisions).",
                file=sys.stderr,
                flush=True,
            )

        # NEW: correct diagnostics
        _dump_available_tools(agent, "on reuse (no reload)")

        if hasattr(agent, "chat_history"):
            try:
                print(f"[AGENT] Chat history: {len(agent.chat_history)} messages", file=sys.stderr, flush=True)
            except Exception:
                pass

        print(f"{'='*80}\n", file=sys.stderr, flush=True)

    return _agents[session_id]
