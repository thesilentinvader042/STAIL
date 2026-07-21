# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared library first
COPY shared /app/shared
RUN pip install --no-cache-dir -e /app/shared

# Install agent dependencies
COPY property-agent/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy agent source
COPY property-agent/agent/ /app/agent/
COPY property-agent/models/ /app/models/
COPY property-agent/tools/ /app/tools/
COPY property-agent/.env.example /app/.env.example

ENV PYTHONPATH=/app

EXPOSE 8004

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8004"]
