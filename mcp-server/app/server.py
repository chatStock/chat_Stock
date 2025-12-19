import logging
from mcp.server.fastmcp import FastMCP

from app.market_client import fetch_quote, fetch_news
from app.stock_logic import shape_stock
from app.news_logic import shape_news_item

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcp-server")

mcp = FastMCP("market-tools", json_response=True)


@mcp.tool(
    description=(
        "Fetch the current market quote for a single stock symbol. "
        "Use this tool when you need the latest price, price change percentage, "
        "or a simple trend indicator (up/down/flat). "
        "Do NOT use this tool for historical prices, charts over time, "
        "or multi-symbol comparisons."
    )
)
async def get_quote(symbol: str) -> dict:
    """
    Returns a structured snapshot of a stock's current market state.
    """
    raw = await fetch_quote(symbol)
    shaped = shape_stock(raw, symbol)
    return shaped.model_dump()


@mcp.tool(
    description=(
        "Retrieve recent news headlines related to a single stock symbol. "
        "Use this tool to explain price movements or market sentiment."
    )
)
async def get_news(symbol: str) -> list[dict]:
    raw_items = await fetch_news(symbol)
    return [shape_news_item(item).model_dump() for item in raw_items]