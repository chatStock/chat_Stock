# agent_stream.py
from typing import AsyncGenerator
import sys
import json
from agent import get_agent


def _safe_repr(obj, max_len=1200):
    try:
        s = repr(obj)
        if len(s) > max_len:
            return s[:max_len] + "...(truncated)"
        return s
    except Exception as e:
        return f"<repr-failed {type(e).__name__}: {e}>"


def _dump_available_tools(agent, label: str):
    try:
        at = getattr(agent, "available_tools", None)
        print(f"[STREAM][DIAG] available_tools attr ({label}) = {type(at)}", file=sys.stderr, flush=True)
        if callable(at):
            val = at()
            print(f"[STREAM][DIAG] available_tools() ({label}) -> {type(val)} = {_safe_repr(val)}",
                  file=sys.stderr, flush=True)
        else:
            print(f"[STREAM][DIAG] available_tools ({label}) -> {_safe_repr(at)}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[STREAM][DIAG] available_tools dump failed ({label}): {type(e).__name__}: {e}",
              file=sys.stderr, flush=True)


def _log_tool_calls(delta, prefix="[STREAM][TOOLCALL]"):
    """Diagnostics: print tool call payloads exactly as emitted by the model."""
    try:
        tc = getattr(delta, "tool_calls", None)
        if not tc:
            return

        for i, call in enumerate(tc):
            # Different SDKs shape this differently; probe safely.
            call_id = getattr(call, "id", None)
            fn = getattr(call, "function", None)
            name = getattr(fn, "name", None) if fn else getattr(call, "name", None)

            args = None
            if fn and hasattr(fn, "arguments"):
                args = fn.arguments
            elif hasattr(call, "arguments"):
                args = call.arguments

            # Try to pretty-print JSON arguments if it's a string.
            pretty_args = args
            if isinstance(args, str):
                try:
                    pretty_args = json.loads(args)
                except Exception:
                    pass

            print(f"{prefix} #{i} id={call_id} name={name} args={_safe_repr(pretty_args)}",
                  file=sys.stderr, flush=True)

    except Exception as e:
        print(f"[STREAM][TOOLCALL] logging failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)


async def stream_agent_reply(session_id: str, user_input: str) -> AsyncGenerator[str, None]:
    agent = await get_agent(session_id)

    print(f"\n{'='*80}", file=sys.stderr, flush=True)
    print(f"[STREAM] NEW REQUEST", file=sys.stderr, flush=True)
    print(f"[STREAM] Session: {session_id}", file=sys.stderr, flush=True)
    print(f"[STREAM] User input: {user_input}", file=sys.stderr, flush=True)
    print(f"[STREAM] Agent object ID: {id(agent)}", file=sys.stderr, flush=True)

    if hasattr(agent, 'tools'):
        print(f"[STREAM] Agent has {len(agent.tools)} tools", file=sys.stderr, flush=True)
    else:
        print(f"[STREAM] WARNING: Agent has no 'tools' attribute", file=sys.stderr, flush=True)

    _dump_available_tools(agent, "before agent.run()")

    print(f"{'='*80}\n", file=sys.stderr, flush=True)

    chunks = []
    item_count = 0
    tool_call_count = 0

    try:
        print(f"[STREAM] Starting agent.run() iteration...", file=sys.stderr, flush=True)

        async for item in agent.run(user_input):
            item_count += 1

            if hasattr(item, "choices") and item.choices:
                for choice in item.choices:
                    if hasattr(choice, "delta") and choice.delta:
                        delta = choice.delta

                        # NEW: log tool calls as they stream in
                        if hasattr(delta, "tool_calls") and delta.tool_calls:
                            tool_call_count += 1
                            _log_tool_calls(delta)

                        if hasattr(delta, "content") and delta.content is not None:
                            chunk = delta.content
                            if chunk:
                                chunks.append(chunk)
                                print(
                                    f"[STREAM] ✓ Chunk: '{chunk[:50]}{'...' if len(chunk) > 50 else ''}'",
                                    file=sys.stderr,
                                    flush=True,
                                )

        print(f"\n[STREAM] ============ ITERATION COMPLETE ============", file=sys.stderr, flush=True)
        print(f"[STREAM] Total items received: {item_count}", file=sys.stderr, flush=True)
        print(f"[STREAM] Tool calls seen: {tool_call_count}", file=sys.stderr, flush=True)
        print(f"[STREAM] Total chunks collected: {len(chunks)}", file=sys.stderr, flush=True)

        if chunks:
            final_response = "".join(chunks).strip()
            print(f"[STREAM] ✓ Yielding response ({len(final_response)} chars)", file=sys.stderr, flush=True)
            yield final_response
        else:
            fallback = (
                "I retrieved the requested data, but couldn't generate a summary. "
                "Please try rephrasing your question."
            )
            print(f"[STREAM] ⚠️  No chunks collected, sending fallback", file=sys.stderr, flush=True)
            yield fallback

    except Exception as e:
        print(f"\n[STREAM][ERROR] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        yield "Sorry, something went wrong while processing your request."
