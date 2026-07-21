FROM python:3.12-slim

WORKDIR /app

# Install dependencies needed for building packages and healthchecks
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy shared library and agent code
COPY shared ./shared
COPY lead-qualification-agent ./lead_qual

# Install both as editable packages
RUN pip install --no-cache-dir -e ./shared
RUN pip install --no-cache-dir -e ./lead_qual

# Set working directory to the agent
WORKDIR /app/lead_qual

EXPOSE 8002

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8002"]
