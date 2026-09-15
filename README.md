# llm-gateway

A local, portable LLM Ops platform: a unified gateway for routing requests
across multiple LLM providers, with caching, cost tracking, rate limiting,
observability, and an evaluation harness — built to run entirely with
Docker Compose on a single machine.

## Status
🚧 Early scaffold — health-check endpoint only.

## Run locally
\```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
\```

Then visit http://localhost:8000/health
