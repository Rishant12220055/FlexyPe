"""
Critical concurrency tests for inventory reservation system.

These tests verify that the system correctly handles race conditions
and prevents overselling even under high concurrent load.
"""
import pytest
import concurrent.futures
import requests
from typing import List
from app.core.redis_client import get_redis_client
from app.core.auth import create_access_token


class TestConcurrency:
    """Test concurrent access patterns."""
    
    BASE_URL = "http://localhost:8000"
    
    def setup_method(self):
        """Setup before each test."""
        self.redis = get_redis_client()
        
    def create_user_token(self, user_id: str) -> str:
        """Create JWT token for user."""
        return create_access_token(user_id)
    
    def attempt_reserve(self, user_id: str, sku: str, quantity: int = 1) -> requests.Response:
        """Attempt to reserve inventory."""
        token = self.create_user_token(user_id)
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/inventory/reserve",
            json={"sku": sku, "quantity": quantity},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        return response
    
    def test_last_item_race_100_users(self):
        """
        CRITICAL TEST: 100 users race for the last item.
        
        Expected:
        - Exactly 1 user gets 201 Created
        - 99 users get 409 Conflict
        - Final inventory is 0 (not negative)
        """
        sku = "TEST-LAST-ITEM"
        
        # Setup: Set inventory to 1
        self.redis.set(f"inventory:{sku}", 1)
        
        # Execute: 100 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(self.attempt_reserve, f"user_{i}", sku)
                for i in range(100)
            ]
            responses = [f.result() for f in futures]
        
        # Collect results
        status_codes = [r.status_code for r in responses]
        success_count = status_codes.count(201)
        conflict_count = status_codes.count(409)
        
        # Assertions
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert conflict_count == 99, f"Expected 99 conflicts, got {conflict_count}"
        
        # Verify inventory is 0, not negative
        final_inventory = int(self.redis.get(f"inventory:{sku}") or 0)
        assert final_inventory == 0, f"Inventory should be 0, got {final_inventory}"
        
        print(f"✅ PASSED: {success_count} success, {conflict_count} conflicts")
        print(f"✅ Final inventory: {final_inventory}")
    
    def test_multiple_items_concurrent_reserve(self):
        """
        Test: 50 users try to reserve 2 items each, inventory is 100.
        
        Expected:
        - All 50 users should succeed
        - Final inventory should be 0
        """
        sku = "TEST-MULTIPLE"
        
        # Setup: Set inventory to 100
        self.redis.set(f"inventory:{sku}", 100)
        
        # Execute: 50 users requesting 2 items each
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(self.attempt_reserve, f"user_{i}", sku, 2)
                for i in range(50)
            ]
            responses = [f.result() for f in futures]
        
        # Collect results
        status_codes = [r.status_code for r in responses]
        success_count = status_codes.count(201)
        
        # All should succeed
        assert success_count == 50, f"Expected 50 successes, got {success_count}"
        
        # Verify inventory
        final_inventory = int(self.redis.get(f"inventory:{sku}") or 0)
        assert final_inventory == 0, f"Inventory should be 0, got {final_inventory}"
        
        print(f"✅ PASSED: All 50 users reserved 2 items each")
        print(f"✅ Final inventory: {final_inventory}")
    
    def test_overselling_impossible(self):
        """
        Test: 100 users race for 10 items.
        
        Expected:
        - Exactly 10 users succeed
        - 90 users get rejected
        - Inventory never goes negative
        """
        sku = "TEST-OVERSELL"
        
        # Setup: Set inventory to 10
        self.redis.set(f"inventory:{sku}", 10)
        
        # Execute: 100 users racing
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(self.attempt_reserve, f"user_{i}", sku, 1)
                for i in range(100)
            ]
            responses = [f.result() for f in futures]
        
        # Collect results
        status_codes = [r.status_code for r in responses]
        success_count = status_codes.count(201)
        conflict_count = status_codes.count(409)
        
        # Assertions
        assert success_count == 10, f"Expected 10 successes, got {success_count}"
        assert conflict_count == 90, f"Expected 90 conflicts, got {conflict_count}"
        
        # Verify inventory is exactly 0
        final_inventory = int(self.redis.get(f"inventory:{sku}") or 0)
        assert final_inventory == 0, f"Inventory should be 0, got {final_inventory}"
        
        print(f"✅ PASSED: {success_count} successes, {conflict_count} rejections")
        print(f"✅ Inventory never went negative: {final_inventory}")
    
    def test_idempotency_duplicate_requests(self):
        """
        Test: Same user makes duplicate requests with same idempotency key.
        
        Expected:
        - Both requests return same reservation_id
        - Inventory only decremented once
        """
        sku = "TEST-IDEMPOTENT"
        idempotency_key = "test-idem-key-123"
        user_id = "user_idem_test"
        
        # Setup
        self.redis.set(f"inventory:{sku}", 10)
        token = self.create_user_token(user_id)
        
        # First request
        response1 = requests.post(
            f"{self.BASE_URL}/api/v1/inventory/reserve",
            json={"sku": sku, "quantity": 2},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": idempotency_key
            }
        )
        
        # Duplicate request
        response2 = requests.post(
            f"{self.BASE_URL}/api/v1/inventory/reserve",
            json={"sku": sku, "quantity": 2},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": idempotency_key
            }
        )
        
        # Both should succeed
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        # Should return same reservation_id
        data1 = response1.json()
        data2 = response2.json()
        assert data1["reservation_id"] == data2["reservation_id"]
        
        # Inventory only decremented once
        final_inventory = int(self.redis.get(f"inventory:{sku}") or 0)
        assert final_inventory == 8, f"Expected inventory 8, got {final_inventory}"
        
        print(f"✅ PASSED: Idempotency working correctly")
        print(f"✅ Same reservation ID: {data1['reservation_id']}")
        print(f"✅ Inventory decremented once: {final_inventory}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
