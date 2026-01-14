# Generated with Claude
# -----------------------------
# Base image
# -----------------------------
FROM python:3.11-slim

# -----------------------------
# Environment
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# -----------------------------
# System deps (minimal)
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Python deps
# -----------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# -----------------------------
# App source
# -----------------------------
COPY . .

# -----------------------------
# Expose FastAPI
# -----------------------------
EXPOSE 8000

# -----------------------------
# Default envs (override in compose)
# -----------------------------
ENV MCP_TRANSPORT=stdio \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

# -----------------------------
# Run FastAPI
# -----------------------------
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]