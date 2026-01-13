import logging
from mcp.server.fastmcp import FastMCP

from app.market_client import fetch_quote, fetch_news
from app.stock_logic import shape_stock
from app.news_logic import shape_news_item
import sys

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcp-server")

print("MCP SERVER BOOTED", file=sys.stderr, flush=True)

# MCP server name MUST match what the agent connects to
mcp = FastMCP("market-tools", json_response=True)

# Added better descriptions for MCP tools and basic fallbacks with ChatGPT

@mcp.tool(
    description=(
        "ONLY tool for retrieving the CURRENT market quote of a SINGLE stock.\n"
        "Input:\n"
        "- symbol: company ticker or name (e.g. 'AIR.PA', 'AAPL', 'Airbus')\n\n"
        "Use this tool when the user asks about:\n"
        "- stock price\n"
        "- price change\n"
        "- market trend\n\n"
        "DO NOT use this tool for news or multiple companies.\n"
        "DO NOT invent other tools."
    )
)
async def get_quote(symbol: str) -> dict:
    log.info(f"[MCP] get_quote invoked | symbol={symbol}")

    raw = await fetch_quote(symbol)
    shaped = shape_stock(raw, symbol)

    result = shaped.model_dump()
    log.info(f"[MCP] get_quote success | result={result}")

    return result


@mcp.tool(
    description=(
        "ONLY tool for retrieving RECENT NEWS about a SINGLE company.\n"
        "Input:\n"
        "- symbol: company name or ticker (e.g. 'Airbus', 'TSLA')\n\n"
        "Use this tool whenever the user asks for:\n"
        "- news\n"
        "- headlines\n"
        "- recent events\n"
        "- company updates\n\n"
        "DO NOT invent other tools.\n"
        "DO NOT answer news questions without calling this tool."
    )
)
async def get_news(symbol: str) -> list[dict]:
    log.info(f"[MCP] get_news invoked | symbol={symbol}")

    raw_items = await fetch_news(symbol)
    log.info(f"[MCP] raw_items={raw_items}")

    # Graceful fallback: NEVER return an empty list silently
    if not raw_items:
        log.warning("[MCP] get_news returned no data")
        return [
            {
                "headline": f"No recent news found for {symbol}",
                "source": "system",
                "published_at": "unknown",
                "impact": "low",
            }
        ]

    shaped = [shape_news_item(item).model_dump() for item in raw_items]
    log.info(f"[MCP] get_news success | count={len(shaped)}")

    return shaped


if __name__ == "__main__":
    log.info("[MCP] Server starting (stdio)")
    mcp.run()