# Recommendation Agent (AGT-05)

> **Cluster:** Discovery & Matching
> **Model:** `llama3-8b-8192`
> **Port:** `8005`

Ranks properties with composite scoring and generates LLM annotations for top results.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Process agent request |
| `GET` | `/info` | Agent metadata |
| `GET` | `/health` | Liveness probe |

## Local Development

```bash
cp .env.example .env
pip install -e ".[dev]"
pip install -e "../shared"
uvicorn agent.main:app --reload --port 8005
```
