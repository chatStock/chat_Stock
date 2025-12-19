FROM python:3.11-slim

# --- basic hygiene ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# --- system deps (minimal) ---
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- python deps ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- app code ---
COPY app app
COPY server.py .

# --- default MCP settings ---
# stdio is the default (Claude Desktop, Cursor, etc.)
ENV MCP_TRANSPORT=stdio
ENV MARKET_API_URL=http://market-data:9000

# IMPORTANT:
# - stdin/stdout must be preserved for MCP stdio transport
# - do NOT wrap in a shell
CMD ["python", "server.py"]