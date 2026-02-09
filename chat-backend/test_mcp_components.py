#!/usr/bin/env python3
"""
Quick test to verify MCP server can start and tools work
Run this inside the backend container to test the MCP layer
"""
import asyncio
import sys
from pathlib import Path

# Add mcp-server to path
mcp_dir = Path(__file__).parent / "mcp-server"
sys.path.insert(0, str(mcp_dir))

print(f"Testing from: {Path(__file__).parent}")
print(f"MCP directory: {mcp_dir}")
print(f"Python path: {sys.path}")
print("-" * 60)

async def test_imports():
    """Test if we can import the MCP modules"""
    print("\n1. Testing imports...")
    try:
        from app import config
        print(f"   ✅ Imported config")
        print(f"   MARKET_API_URL: {config.MARKET_API_URL}")
    except Exception as e:
        print(f"   ❌ Failed to import config: {e}")
        return False
    
    try:
        from app import market_client
        print(f"   ✅ Imported market_client")
    except Exception as e:
        print(f"   ❌ Failed to import market_client: {e}")
        return False
    
    return True

async def test_market_client():
    """Test if market_client can reach market-api"""
    print("\n2. Testing market_client functions...")
    
    from app.market_client import fetch_quote, fetch_news
    from app.config import MARKET_API_URL
    
    print(f"   Target: {MARKET_API_URL}")
    
    # Test quote
    try:
        print("\n   Testing fetch_quote('AAPL')...")
        result = await fetch_quote("AAPL")
        print(f"   ✅ fetch_quote succeeded")
        print(f"      Current price: {result.get('c')}")
        print(f"      Previous close: {result.get('pc')}")
    except Exception as e:
        print(f"   ❌ fetch_quote failed: {e}")
        return False
    
    # Test news
    try:
        print("\n   Testing fetch_news('AAPL')...")
        result = await fetch_news("AAPL")
        print(f"   ✅ fetch_news succeeded")
        print(f"      Found {len(result)} news items")
        if result:
            print(f"      Latest: {result[0].get('headline', 'N/A')[:60]}...")
    except Exception as e:
        print(f"   ❌ fetch_news failed: {e}")
        return False
    
    return True

async def test_mcp_tools():
    """Test if MCP server tools work"""
    print("\n3. Testing MCP server tools...")
    
    try:
        from app.server import get_quote, get_news
        print("   ✅ Imported MCP tools")
    except Exception as e:
        print(f"   ❌ Failed to import MCP tools: {e}")
        return False
    
    # Test get_quote
    try:
        print("\n   Testing get_quote('AAPL')...")
        result = await get_quote("AAPL")
        print(f"   ✅ get_quote succeeded")
        print(f"      Symbol: {result.get('symbol')}")
        print(f"      Price: {result.get('current_price')}")
        print(f"      Trend: {result.get('trend')}")
    except Exception as e:
        print(f"   ❌ get_quote failed: {e}")
        return False
    
    # Test get_news
    try:
        print("\n   Testing get_news('AAPL')...")
        result = await get_news("AAPL")
        print(f"   ✅ get_news succeeded")
        print(f"      Found {len(result)} shaped news items")
        if result:
            print(f"      Latest: {result[0].get('headline', 'N/A')[:60]}...")
    except Exception as e:
        print(f"   ❌ get_news failed: {e}")
        return False
    
    return True

async def main():
    print("=" * 60)
    print("MCP SERVER COMPONENT TEST")
    print("=" * 60)
    
    success = True
    
    # Run tests in order
    if not await test_imports():
        print("\n❌ Import test failed - cannot continue")
        sys.exit(1)
    
    if not await test_market_client():
        print("\n❌ Market client test failed")
        success = False
    
    if not await test_mcp_tools():
        print("\n❌ MCP tools test failed")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe MCP server components are working correctly.")
        print("If requests still don't happen, the issue is in the agent")
        print("spawning the MCP server subprocess.")
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nFix the failed components before debugging further.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)