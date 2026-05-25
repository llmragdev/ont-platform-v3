import random
from locust import HttpUser, task, between

class Phase3PerformanceTest(HttpUser):
    wait_time = between(0.1, 1.0)  # Simulate real user thinking time
    
    # Custom headers representing user roles
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": "perf_user@nipa.go.kr",
        "X-Company-Id": "demo-co",
        "X-Project-Id": "proj-01",
        "X-Role": "Admin"
    }

    @task(2)
    def execute_action(self):
        """Scenario 1: Execute change_deadline action (repeatable on same entity)"""
        self.client.post(
            "/api/workflow/execute",
            headers=self.headers,
            json={
                "doc_id": "ai-voucher-2025",
                "entity_id": "P001AAA",
                "action": "change_deadline",
                "domain_id": "ai-voucher-2025",
                "params": {
                    "new_deadline": f"2027-{random.randint(1,12):02d}-31"
                }
            }
        )

    @task(3)
    def query_changelog(self):
        """Scenario 2: GET /api/changelog/history with pagination"""
        self.client.get(
            "/api/changelog/history?page=1&page_size=50",
            headers=self.headers
        )

    @task(1)
    def get_statistics(self):
        """Scenario 3: GET /api/writeback/statistics"""
        self.client.get(
            "/api/writeback/statistics",
            headers=self.headers
        )
