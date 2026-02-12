# chat_Stock

chat_Stock is a multi-service stock chat application with:
- React frontend (`chat-frontend`)
- Python chat backend and MCP tools (`chat-backend`)
- Python market data API (`market-api`)
- Monitoring with Prometheus and Grafana (`monitoring`)

This repository supports two runtime modes:
- Docker Compose for local full-stack runs
- Kubernetes manifests in `k8s/` for cluster deployment demos

## Architecture

### Docker Compose (local dev)

```text
frontend (5173) -> backend (8000) -> market-api (9000) -> Finnhub
                                     |
                                     +-> /metrics -> prometheus (9090) -> grafana (3000)
```

### Kubernetes (demo branch)

```text
frontend Deployment/Service (frontend-service:5173)
  -> backend Deployment/Service (backend-service:8000)
    -> market-api Deployment/Service (market-api-service:9000)
      -> Finnhub external API

prometheus Deployment/Service (prometheus-service:9090)
  scrapes:
  - market-api-service:9000/metrics
  - localhost:9090 (self)

grafana Deployment/Service (grafana-service:3000)
  datasource: Prometheus
  dashboard: market-api-dashboard.json (provisioned via ConfigMap)
```

## Prometheus Data Sources

Prometheus is configured to scrape:
- `market-api` metrics endpoint: `/metrics`
- Prometheus self-metrics

Current config locations:
- Compose: `monitoring/prometheus.yml`
- Kubernetes: `k8s/prometheus.yaml` (ConfigMap `prometheus-config`)

Important: the backend is not currently scraped by Prometheus in these configs.

## Repo Structure

```text
.
|-- chat-frontend/
|-- chat-backend/
|-- market-api/
|-- monitoring/
|-- k8s/
|-- .github/workflows/
|-- docker-compose.yml
`-- README_k8s.md
```

## Run With Docker Compose

```bash
docker compose up --build
```

Services:
- frontend
- backend
- market-api
- prometheus
- grafana

## Run With Kubernetes

See `README_k8s.md` for the exact workflow and `kubectl` commands.

## CI

Workflow file: `.github/workflows/ci.yml`

Current CI responsibilities:
- Branch policy checks for PR targets
- Backend tests
- Market API tests

Note: CI currently does not deploy to Kubernetes (no CD job in `ci.yml`).

## Tests

Run backend tests:

```bash
cd chat-backend
pytest
```

Run market API tests:

```bash
cd market-api
pytest
```
