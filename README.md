# chat_Stock

#### Figure 1 — Docker Compose architecture of chat_Stock
```
╔══════════════════════════════════════════════════════════════════════╗
║                         Docker Compose Network                       ║
║                                                                      ║
║  ┌──────────────────────────┐                                        ║
║  │      chat-frontend       │                                        ║
║  │──────────────────────────│                                        ║
║  │  • React (Vite build)    │                                        ║
║  │  • Nginx static server   │                                        ║
║  │  • / → UI                │                                        ║
║  └───────────┬──────────────┘                                        ║
║              │  HTTP                                                 ║
║              ▼                                                       ║
║  ┌──────────────────────────┐        ┌──────────────────────────┐    ║
║  │       chat-backend       │ ─────▶ │        market-api        │   ║
║  │──────────────────────────│  HTTP  │──────────────────────────│    ║
║  │  • Agent orchestration   │        │  • Finnhub wrapper       │    ║
║  │  • MCP tools             │        │  • /quote   /news        │    ║
║  │  • Streaming responses   │        │  • /metrics              │    ║
║  └───────────┬──────────────┘        └───────────┬──────────────┘    ║
║              │                                   │  HTTPS            ║
║              ▼                                   ▼                   ║
║  ┌──────────────────────────┐              ( Finnhub API )           ║
║  │        prometheus        │                                        ║
║  │──────────────────────────│                                        ║
║  │  • Metrics store         │ ◀─────────── /metrics ────────────────╢
║  └───────────┬──────────────┘                                        ║
║              │                                                       ║
║              ▼                                                       ║
║  ┌──────────────────────────────────────────────────────────┐        ║
║  │                         grafana                          │        ║
║  │──────────────────────────────────────────────────────────│        ║
║  │  • Dashboards                                            │        ║
║  │  • Latency / tool calls / errors                         │        ║
║  └──────────────────────────────────────────────────────────┘        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

```

## What is this repo?

chat_Stock is a basic multi-service stock market chat application composed of:

* a React frontend
* a Python backend handling agent logic (MCP)
* a separate market data API
* monitoring via Prometheus and Grafana

All services are orchestrated with Docker Compose.

The use case is simple: you can ask for news or recent stock information about a company. 
Future work could implement a temporal dimension to the MCP tools, but for now, the goal is to provide a working MVP for coursework.

---

## Repo structure

```text
.
├── chat-frontend/        # React (Vite) frontend
├── chat-backend/         # Agent orchestration + MCP tools
├── market-api/           # Stock / market data API
├── monitoring/           # Prometheus & Grafana configs
├── docker-compose.yml
└── .github/workflows/    # CI
```

---

## How to run

### Full stack (recommended)

```bash
docker compose up --build
```

This starts:

* frontend
* backend
* market-api
* prometheus
* grafana

---

### Run services individually (dev)

Frontend:

```bash
cd chat-frontend
npm install
npm run dev
```

Backend:

```bash
cd chat-backend
uvicorn api:app --reload
```

Market API:

```bash
cd market-api
python app.py
```

---

## Development workflow

* Do **not** push directly to `main`
* Open PRs against `dev`
* Only `dev` may be merged into `main`

These rules are enforced by CI.

---

## CI

CI runs on pull requests and enforces:

* branch flow (`dev → main` only)
* backend unit tests

CI configuration lives in:

```text
.github/workflows/
```

---

## Tests

Backend tests use `pytest`.

Run locally:

(example, backend)
```bash
cd chat-backend
pytest
```

Tests are also run automatically in CI.

---

## Monitoring
> TODO

