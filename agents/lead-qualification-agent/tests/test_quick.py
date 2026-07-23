import os
os.environ.setdefault("GROQ_API_KEY", "test-key")

from agent.main import app
from fastapi.testclient import TestClient

with TestClient(app, raise_server_exceptions=False) as client:
    response = client.post("/chat", json={"agent_id": "AGT-02", "message": "test"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")