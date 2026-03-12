import logging
from datetime import date
from decimal import Decimal
from uuid import uuid4

from locust import HttpUser, between, task

# --- Locustfile for API Performance Testing ---

# Global variable to store the root ID of the pre-created hierarchy
# This needs to be managed carefully in a distributed Locust setup.
# For a single-process local run, this is sufficient.
HIERARCHY_ROOT_ID = None
HIERARCHY_DEPTH = 5 # Number of levels in the hierarchy (including root)
HIERARCHY_CHILDREN_PER_LEVEL = 1 # Simple 1:1 hierarchy for initial test

logger = logging.getLogger(__name__)

class AccountAPIUser(HttpUser):
    """
    User class for simulating client requests to the Account API.
    Tests performance of account creation, retrieval, and balance adjustment.
    """
    wait_time = between(1, 5) # Simulate user thinking time between requests

    def on_start(self):
        """on_start is called when a Locust user starts"""
        logger.info("Locust user starting...")
        self.account_id = None # Account for single-account operations

        # Ensure a hierarchy exists for performance testing
        self._create_hierarchy_if_not_exists()

        # Create an account to be used in GET/PUT/DELETE tests if it doesn't already exist
        try:
            # Check if a test account already exists using a predictable name
            test_account_name = "Locust Single Test Account"
            response = self.client.get(f"/accounts?search_term={test_account_name}")
            if response.status_code == 200 and response.json():
                self.account_id = response.json()[0]["id"]
                logger.info(f"Using existing single account for testing: {self.account_id}")
            else:
                create_payload = {
                    "name": test_account_name,
                    "account_number": f"LOCUST_SINGLE_{uuid4()}",
                    "currency": "USD",
                    "accounting_category": "ASSET",
                    "banking_product_type": "BANK",
                    "available_balance": str(Decimal("1000.00")),
                    "credit_limit": None,
                    "notes": "Locust test account for single operations",
                    "hidden": False,
                    "placeholder": False
                }
                create_response = self.client.post("/accounts/", json=create_payload)
                if create_response.status_code == 201:
                    self.account_id = create_response.json()["id"]
                    logger.info(f"Locust user created single account for testing: {self.account_id}")
                else:
                    logger.error(f"Failed to create single account for testing: {create_response.status_code} - {create_response.text}")

        except Exception as e:
            logger.error(f"Error during Locust on_start: {e}")

    def _create_hierarchy_if_not_exists(self):
        """Creates a deep account hierarchy if it doesn't exist."""
        global HIERARCHY_ROOT_ID
        if HIERARCHY_ROOT_ID:
            # Verify it actually exists
            response = self.client.get(f"/accounts/{HIERARCHY_ROOT_ID}")
            if response.status_code == 200:
                logger.info(f"Using existing hierarchy with root: {HIERARCHY_ROOT_ID}")
                return

        logger.info("Creating a new account hierarchy for performance testing...")

        current_parent_id = None
        for i in range(HIERARCHY_DEPTH):
            account_name = f"Hierarchy Level {i+1} - {uuid4()}"
            create_payload = {
                "name": account_name,
                "currency": "USD",
                "accounting_category": "ASSET",
                "available_balance": str(Decimal("100.00")),
                "parent_account_id": current_parent_id,
                "placeholder": False
            }
            response = self.client.post("/accounts/", json=create_payload)
            if response.status_code == 201:
                new_account_id = response.json()["id"]
                if i == 0:
                    HIERARCHY_ROOT_ID = new_account_id
                current_parent_id = new_account_id
            else:
                logger.error(f"Failed to create hierarchy account at level {i+1}: {response.status_code} - {response.text}")
                # Abort hierarchy creation if any level fails
                HIERARCHY_ROOT_ID = None
                return
        logger.info(f"Hierarchy created with root: {HIERARCHY_ROOT_ID}")

    @task(10) # Higher weight means this task is executed more frequently
    def get_account(self):
        """Task for fetching a single account by ID."""
        if self.account_id:
            with self.client.get(f"/accounts/{self.account_id}", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Get single account failed with status {response.status_code}")

    @task(5)
    def get_account_hierarchy(self):
        """Task for fetching the root of a deep account hierarchy."""
        if HIERARCHY_ROOT_ID:
            with self.client.get(f"/accounts/{HIERARCHY_ROOT_ID}", catch_response=True) as response:
                if response.status_code == 200:
                    # Optional: Verify hierarchy_balance is present and reasonable
                    response_data = response.json()
                    if "hierarchy_balance" not in response_data:
                        response.failure("Hierarchy balance not found in response")
                    # No explicit timing assertion here, Locust handles that.
                else:
                    response.failure(f"Get hierarchy failed with status {response.status_code}")
        else:
            logger.warning("HIERARCHY_ROOT_ID not set, skipping get_account_hierarchy task.")


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
        with self.client.post("/accounts/", json=account_data, catch_response=True) as response:
            if response.status_code != 201:
                response.failure(f"Create account failed with status {response.status_code}")

    @task(3) # Moderate weight for adjustment
    def adjust_account_balance(self):
        """Task for adjusting an account balance."""
        if self.account_id:
            target_balance = str(Decimal("1200.75")) # Example new balance
            adjustment_payload = {
                "target_balance": target_balance, # Use target_balance
                "adjustment_date": date.today().isoformat(),
                "description": "Locust balance adjustment",
                "action_type": "ADJUSTMENT"
            }
            with self.client.post(f"/accounts/{self.account_id}/adjust_balance", json=adjustment_payload, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Adjust balance failed with status {response.status_code}")
        else:
            logger.warning("self.account_id not set, skipping adjust_account_balance task.")

# --- Example of how to run Locust ---
# 1. Save this file as locustfile.py in the project root.
# 2. Ensure your FastAPI application is running (e.g., `uvicorn src.main:app --reload` or similar).
#    The default host for Locust is http://localhost:8000. You might need to configure it.
# 3. Run Locust from your terminal: locust -f locustfile.py
# 4. Access the Locust web UI (usually http://localhost:8089) to start the test.
