# llm-gateway

A local, portable LLM Ops platform: a unified gateway for routing requests
across multiple LLM providers, with caching, cost tracking, rate limiting,
observability, and an evaluation harness — built to run entirely with
Docker Compose on a single machine.

## Status
🚧 Early scaffold — health-check endpoint only.

## Run locally

### Option A: Docker Compose (recommended)
```bash
docker compose up --build
```
Visit http://localhost:8000/health

### Option B: Python venv
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Development

Install dev tools (linting, formatting):
```bash
pip install -r requirements-dev.txt
ruff check .
```

## Observability

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin, or anonymous viewer access)
