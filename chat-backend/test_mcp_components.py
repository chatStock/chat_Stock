#!/usr/bin/env python3
"""
Pytest-compatible MCP component tests
These run in CI alongside other pytest tests
"""
import pytest
import httpx
import sys
from pathlib import Path

# Add mcp-server to path
mcp_dir = Path(__file__).parent / "mcp-server"
sys.path.insert(0, str(mcp_dir))


@pytest.mark.asyncio
async def test_imports():
    """Test if we can import the MCP modules"""
    # Import config
    from app import config
    assert config.MARKET_API_URL is not None, "MARKET_API_URL should be set"
    print(f"   ✅ Imported config")
    print(f"   MARKET_API_URL: {config.MARKET_API_URL}")
    
    # Import market_client
    from app import market_client
    assert market_client is not None
    print(f"   ✅ Imported market_client")


@pytest.mark.asyncio
async def test_market_client(respx_mock):
    """Test if market_client can reach market-api"""
    from app.market_client import fetch_quote, fetch_news
    from app.config import MARKET_API_URL
    
    print(f"   Target: {MARKET_API_URL}")
    
    # Mock the quote endpoint
    respx_mock.get(f"{MARKET_API_URL}/quote").mock(
        return_value=httpx.Response(200, json={
            "c": 192.17,
            "pc": 185.50,
            "t": 1707494400
        })
    )
    
    # Mock the news endpoint
    respx_mock.get(f"{MARKET_API_URL}/news").mock(
        return_value=httpx.Response(200, json=[
            {
                "headline": "Test headline for AAPL",
                "source": "Test Source",
                "datetime": 1707494400
            }
        ])
    )
    
    # Test quote
    print("\n   Testing fetch_quote('AAPL')...")
    result = await fetch_quote("AAPL")
    assert "c" in result, "Quote should contain current price (c)"
    assert "pc" in result, "Quote should contain previous close (pc)"
    print(f"   ✅ fetch_quote succeeded")
    print(f"      Current price: {result.get('c')}")
    print(f"      Previous close: {result.get('pc')}")
    
    # Test news
    print("\n   Testing fetch_news('AAPL')...")
    result = await fetch_news("AAPL")
    assert isinstance(result, list), "News should return a list"
    print(f"   ✅ fetch_news succeeded")
    print(f"      Found {len(result)} news items")
    if result:
        print(f"      Latest: {result[0].get('headline', 'N/A')[:60]}...")


@pytest.mark.asyncio
async def test_mcp_tools(respx_mock):
    """Test if MCP server tools work"""
    from app.server import get_quote, get_news
    from app.config import MARKET_API_URL
    print("   ✅ Imported MCP tools")
    
    # Mock the quote endpoint
    respx_mock.get(f"{MARKET_API_URL}/quote").mock(
        return_value=httpx.Response(200, json={
            "c": 192.17,
            "pc": 185.50,
            "t": 1707494400
        })
    )
    
    # Mock the news endpoint
    respx_mock.get(f"{MARKET_API_URL}/news").mock(
        return_value=httpx.Response(200, json=[
            {
                "headline": "Test headline for AAPL",
                "source": "Test Source",
                "datetime": 1707494400
            }
        ])
    )
    
    # Test get_quote
    print("\n   Testing get_quote('AAPL')...")
    result = await get_quote("AAPL")
    assert "symbol" in result, "Result should contain symbol"
    assert "current_price" in result, "Result should contain current_price"
    assert "trend" in result, "Result should contain trend"
    print(f"   ✅ get_quote succeeded")
    print(f"      Symbol: {result.get('symbol')}")
    print(f"      Price: {result.get('current_price')}")
    print(f"      Trend: {result.get('trend')}")
    
    # Test get_news
    print("\n   Testing get_news('AAPL')...")
    result = await get_news("AAPL")
    assert isinstance(result, list), "News should return a list"
    assert len(result) > 0, "News should return at least one item"
    print(f"   ✅ get_news succeeded")
    print(f"      Found {len(result)} shaped news items")
    if result:
        assert "headline" in result[0], "News items should contain headline"
        print(f"      Latest: {result[0].get('headline', 'N/A')[:60]}...")