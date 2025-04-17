from locust import HttpUser, task, between
import os

class BankingUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def create_transaction(self):
        token = os.getenv("CUSTOMER_TOKEN", "your-customer-token")
        self.client.post("/transactions", 
                        json={"amount": 100.0, "transaction_type": "deposit"},
                        headers={"Authorization": f"Bearer {token}"})