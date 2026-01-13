import pytest
from app.server import get_quote

@pytest.mark.asyncio
async def test_get_quote_tool(monkeypatch):
    async def fake_fetch(symbol):
        return {"c": 100, "pc": 100, "t": 0}

    monkeypatch.setattr("app.server.fetch_quote", fake_fetch)

    result = await get_quote("AAPL")

    assert result["symbol"] == "AAPL"
    assert result["trend"] == "flat"