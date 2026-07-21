FROM pgvector/pgvector:pg17

# Install PostGIS on top of pgvector for Postgres 17 (supports arm64 + amd64)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-17-postgis-3 \
    && rm -rf /var/lib/apt/lists/*
