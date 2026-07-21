# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared library first
COPY shared /app/shared
RUN pip install --no-cache-dir -e /app/shared

# Install agent dependencies
COPY buyer-agent/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy agent source
COPY buyer-agent/agent/ /app/agent/
COPY buyer-agent/models/ /app/models/
COPY buyer-agent/tools/ /app/tools/
COPY buyer-agent/.env.example /app/.env.example

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8003"]
