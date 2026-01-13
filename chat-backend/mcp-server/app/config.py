import os

MARKET_API_URL = os.getenv("MARKET_API_URL", "http://localhost:9000")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "3.0"))

# MCP transport:
# - "stdio" for Claude Desktop / local tool hosts
# - "streamable-http" to expose http://host:8000/mcp
TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))