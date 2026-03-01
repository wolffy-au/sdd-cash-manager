from datetime import date
from decimal import Decimal
from uuid import uuid4

from locust import HttpUser, between, task

# --- Locustfile for API Performance Testing ---

class AccountAPIUser(HttpUser):
    """
    User class for simulating client requests to the Account API.
    Tests performance of account creation, retrieval, and balance adjustment.
    """
    wait_time = between(1, 5) # Simulate user thinking time between requests

    def on_start(self):
        """on_start is called when a Locust user starts"""
        # Optionally, create a user or do initial setup if needed.
        # For simplicity, we'll assume accounts can be created on the fly or pre-created.
        # We'll create an account here to use for GET/PUT/DELETE tests.
        # This might require careful handling if tests run in parallel or need specific states.

        # Let's pre-create an account for GET/PUT/DELETE tests to ensure it exists.
        # This might not be ideal for pure performance testing of creation,
        # but useful for testing GET/PUT/DELETE endpoints.
        print("Locust user starting...")
        # Create an account to be used in GET/PUT/DELETE tests
        self.account_id = None
        try:
            # We need to ensure the API is running and accessible at self.host
            # For local testing, self.host would be http://localhost:8000 or similar.
            # In this environment, we can't directly run the API.
            # Thus, these tests are illustrative and would require a running API.

            # Illustrative account creation for GET/PUT/DELETE tests
            # POST /accounts/
            create_payload = {
                "name": "Locust Test Account",
                "account_number": f"LOCUST_{uuid4()}",
                "currency": "USD",
                "accounting_category": "ASSET",
                "banking_product_type": "BANK",
                "available_balance": "1000.00",
                "credit_limit": None,
                "notes": "Locust test account",
                "hidden": False,
                "placeholder": False
            }
            create_response = self.client.post("/accounts/", json=create_payload)
            if create_response.status_code == 201:
                self.account_id = create_response.json()["id"]
                print(f"Locust user created account for testing: {self.account_id}")
            else:
                print(f"Failed to create account for testing: {create_response.status_code} - {create_response.text}")
                # Depending on scenario, might want to fail the test or skip dependent tasks.

        except Exception as e:
            print(f"Error during Locust on_start: {e}")
            # Handle exceptions if API is not reachable or errors occur

    @task(10) # Higher weight means this task is executed more frequently
    def get_account(self):
        """Task for fetching an account by ID."""
        if self.account_id:
            try:
                self.client.get(f"/accounts/{self.account_id}")
            except Exception as e:
                print(f"Error during GET account: {e}")

    @task(5) # Lower weight for creation, as it might be tested less frequently or separately
    def create_account(self):
        """Task for creating a new account."""
        account_data = {
            "name": f"Locust Account {uuid4()}",
            "account_number": f"LOCUSTACC_{uuid4()}",
            "currency": "USD",
            "accounting_category": "ASSET",
            "banking_product_type": "BANK",
            "available_balance": str(Decimal("500.00")), # Ensure Decimal is string for JSON
            "credit_limit": None,
            "notes": "Locust generated",
            "hidden": False,
            "placeholder": False
        }
        try:
            self.client.post("/accounts/", json=account_data)
        except Exception as e:
            print(f"Error during POST account: {e}")

    @task(3) # Moderate weight for adjustment
    def adjust_account_balance(self):
        """Task for adjusting an account balance."""
        if self.account_id:
            adjustment_payload = {
                "new_balance": str(Decimal("1200.75")), # Example new balance
                "adjustment_date": date.today().isoformat(),
                "description": "Locust balance adjustment"
            }
            try:
                self.client.post(f"/accounts/{self.account_id}/adjust_balance", json=adjustment_payload)
            except Exception as e:
                print(f"Error during POST adjust_balance: {e}")

    # Example of updating - might be less frequent or separated
    # @task(1)
    # def update_account(self):
    #     """Task for updating an account."""
    #     if self.account_id:
    #         update_payload = {
    #             "notes": "Locust updated notes"
    #         }
    #         try:
    #             self.client.put(f"/accounts/{self.account_id}", json=update_payload)
    #         except Exception as e:
    #             print(f"Error during PUT account: {e}")

    # DELETE tasks are usually not run in performance tests unless specifically testing deletion load.
    # def on_stop(self):
    #     """on_stop is called when the TaskSet is stopped"""
    #     # Clean up the created account if needed
    #     if self.account_id:
    #         try:
    #             self.client.delete(f"/accounts/{self.account_id}")
    #             print(f"Locust user cleaned up account: {self.account_id}")
    #         except Exception as e:
    #             print(f"Error during DELETE account cleanup: {e}")

# --- Example of how to run Locust ---
# 1. Save this file as locustfile.py in the project root.
# 2. Ensure your FastAPI application is running (e.g., `uvicorn src.main:app --reload` or similar).
#    The default host for Locust is http://localhost:8000. You might need to configure it.
# 3. Run Locust from your terminal: locust -f locustfile.py
# 4. Access the Locust web UI (usually http://localhost:8089) to start the test.
