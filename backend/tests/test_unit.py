"""Unit tests for reservation service."""
import pytest
from unittest.mock import Mock, patch
from app.services.reservation_service import ReservationService, InsufficientInventoryError
from app.models.schemas import ReservationData


class TestReservationService:
    """Test reservation service logic."""
    
    def setup_method(self):
        """Setup before each test."""
        self.service = ReservationService()
    
    def test_reserve_inventory_success(self):
        """Test successful inventory reservation."""
        sku = "TEST-SKU-001"
        quantity = 2
        user_id = "user_123"
        
        # Setup: Set initial inventory
        self.service.set_inventory(sku, 10)
        
        # Reserve
        reservation_id, expires_at = self.service.reserve_inventory(
            sku=sku,
            quantity=quantity,
            user_id=user_id
        )
        
        # Verify reservation created
        assert reservation_id is not None
        assert reservation_id.startswith("rsv_")
        assert expires_at is not None
        
        # Verify inventory decremented
        status = self.service.get_inventory_status(sku)
        assert status["available"] == 8
    
    def test_reserve_insufficient_inventory(self):
        """Test reservation fails when insufficient inventory."""
        sku = "TEST-SKU-002"
        quantity = 5
        user_id = "user_123"
        
        # Setup: Low inventory
        self.service.set_inventory(sku, 2)
        
        # Attempt to reserve more than available
        with pytest.raises(InsufficientInventoryError) as exc_info:
            self.service.reserve_inventory(
                sku=sku,
                quantity=quantity,
                user_id=user_id
            )
        
        # Verify error contains available count
        assert exc_info.value.available == 2
        
        # Verify inventory unchanged
        status = self.service.get_inventory_status(sku)
        assert status["available"] == 2
    
    def test_confirm_reservation_success(self):
        """Test successful reservation confirmation."""
        sku = "TEST-SKU-003"
        user_id = "user_123"
        
        # Setup and reserve
        self.service.set_inventory(sku, 10)
        reservation_id, _ = self.service.reserve_inventory(sku, 2, user_id)
        
        # Confirm reservation
        reservation = self.service.confirm_reservation(reservation_id, user_id)
        
        # Verify reservation data
        assert reservation.user_id == user_id
        assert reservation.sku == sku
        assert reservation.quantity == 2
        
        # Verify reservation deleted
        assert self.service.get_reservation(reservation_id) is None
    
    def test_confirm_reservation_wrong_user(self):
        """Test confirmation fails for wrong user."""
        sku = "TEST-SKU-004"
        user_id = "user_123"
        other_user = "user_456"
        
        # Setup and reserve
        self.service.set_inventory(sku, 10)
        reservation_id, _ = self.service.reserve_inventory(sku, 2, user_id)
        
        # Attempt to confirm as different user
        with pytest.raises(ValueError) as exc_info:
            self.service.confirm_reservation(reservation_id, other_user)
        
        assert "another user" in str(exc_info.value).lower()
    
    def test_release_expired_reservation(self):
        """Test releasing expired reservation restores inventory."""
        sku = "TEST-SKU-005"
        user_id = "user_123"
        
        # Setup and reserve
        self.service.set_inventory(sku, 10)
        reservation_id, _ = self.service.reserve_inventory(sku, 3, user_id)
        
        # Verify inventory decremented
        status = self.service.get_inventory_status(sku)
        assert status["available"] == 7
        
        # Release reservation
        released = self.service.release_reservation(reservation_id)
        assert released is True
        
        # Verify inventory restored
        status = self.service.get_inventory_status(sku)
        assert status["available"] == 10
        
        # Verify reservation deleted
        assert self.service.get_reservation(reservation_id) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
