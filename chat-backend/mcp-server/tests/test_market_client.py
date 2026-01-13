import pytest
import respx
from httpx import Response

from app.market_client import fetch_quote, fetch_news

@pytest.mark.asyncio
@respx.mock
async def test_fetch_quote():
    respx.get("http://localhost:9000/quote").mock(
        return_value=Response(
            200,
            json={"c": 100, "pc": 90, "t": 1700000000},
        )
    )

    data = await fetch_quote("AAPL")
    assert data["c"] == 100


@pytest.mark.asyncio
@respx.mock
async def test_fetch_news():
    respx.get("http://localhost:9000/news").mock(
        return_value=Response(
            200,
            json=[
                {"headline": "News", "source": "Test", "datetime": 1700000000}
            ],
        )
    )

    data = await fetch_news("AAPL")
    assert isinstance(data, list)
    assert data[0]["headline"] == "News"