import httpx
from .config import MARKET_API_URL, REQUEST_TIMEOUT


async def fetch_quote(symbol: str) -> dict:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MARKET_API_URL}/quote", params={"symbol": symbol})
        r.raise_for_status()
        return r.json()


async def fetch_news(symbol: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.get(f"{MARKET_API_URL}/news", params={"symbol": symbol})
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            raise ValueError("Upstream /news must return a JSON list")
        return data