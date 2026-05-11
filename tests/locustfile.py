from locust import HttpUser, task, between

class SovereignUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.client.headers.update({"X-API-Key": "sk-sovereign-admin"})

    @task(3)
    def chat_request(self):
        """Standard chat load test."""
        self.client.post("/v1/chat", json={
            "message": "Analyze this sovereign infrastructure.",
            "use_rag": False
        })

    @task(1)
    def quick_chat(self):
        """IoT-style quick chat load test."""
        self.client.post("/v1/chat/quick", json={
            "message": "Status check"
        })

    @task(1)
    def get_stats(self):
        """Admin stats load test."""
        self.client.get("/admin/stats")
