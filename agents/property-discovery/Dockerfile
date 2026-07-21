# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared library first (local path mount in compose)
COPY shared /app/shared
RUN pip install --no-cache-dir -e /app/shared

# Install agent dependencies
COPY property-discovery/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy agent source
COPY property-discovery/agent/ /app/agent/
COPY property-discovery/.env.example /app/.env.example
COPY property-discovery/ .

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8001"]
