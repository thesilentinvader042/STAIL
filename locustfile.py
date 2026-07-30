from locust import HttpUser, task, between

class PropertyOSUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def browse_properties(self):
        self.client.get("/api/v1/properties/?city=Mumbai&page=1")

    @task(2)
    def load_crm_leads(self):
        self.client.get("/api/v1/leads/")

    @task(1)
    def load_chat_sessions(self):
        self.client.get("/api/v1/agents/sessions/")

    @task(1)
    def orchestrate_chat(self):
        payload = {
            "message": "3BHK in Bandra under 2.5 Crore",
            "context": {}
        }
        self.client.post("/api/v1/agents/orchestrate", json=payload)
