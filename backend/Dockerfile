# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy memory_system into the container and install its runtime dependencies.
COPY memory_system/ /app/memory_system/
RUN pip install --no-cache-dir -r /app/memory_system/requirements.txt

# Install backend dependencies
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy backend source (includes alembic.ini at root, alembic/ dir, app/ dir, entrypoint.sh)
COPY backend/ .

# /app/memory_system is on PYTHONPATH so bare imports resolve.
ENV PYTHONPATH=/app:/app/memory_system

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
