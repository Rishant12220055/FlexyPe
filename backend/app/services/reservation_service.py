import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.core.redis_client import get_redis_client, RESERVE_INVENTORY_SCRIPT, RESTORE_INVENTORY_SCRIPT
from app.core.config import get_settings
from app.models.schemas import ReservationData
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class InsufficientInventoryError(Exception):
    """Raised when requested quantity exceeds available inventory."""
    def __init__(self, available: int):
        self.available = available
        super().__init__(f"Insufficient inventory. Available: {available}")


class ReservationService:
    """Service for managing inventory reservations with atomic operations."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.reserve_script = self.redis.register_script(RESERVE_INVENTORY_SCRIPT)
        self.restore_script = self.redis.register_script(RESTORE_INVENTORY_SCRIPT)
    
    def _get_inventory_key(self, sku: str) -> str:
        """Get Redis key for inventory."""
        return f"inventory:{sku}"
    
    def _get_reservation_key(self, reservation_id: str) -> str:
        """Get Redis key for reservation."""
        return f"reservation:{reservation_id}"
    
    def _get_idempotency_key(self, key: str) -> str:
        """Get Redis key for idempotency cache."""
        return f"idempotency:{key}"
    
    def check_idempotency(self, idempotency_key: str) -> Optional[dict]:
        """
        Check if request with this idempotency key was already processed.
        
        Args:
            idempotency_key: Unique key for request
            
        Returns:
            Cached response if exists, None otherwise
        """
        if not idempotency_key:
            return None
        
        cached = self.redis.get(self._get_idempotency_key(idempotency_key))
        if cached:
            logger.info(f"Idempotent request detected: {idempotency_key}")
            return json.loads(cached)
        
        return None
    
    def reserve_inventory(
        self,
        sku: str,
        quantity: int,
        user_id: str,
        idempotency_key: Optional[str] = None
    ) -> Tuple[str, datetime]:
        """
        Atomically reserve inventory for a user.
        
        This uses a Lua script to ensure atomic check-and-decrement,
        preventing race conditions and overselling.
        
        Args:
            sku: Product SKU
            quantity: Quantity to reserve
            user_id: User making the reservation
            idempotency_key: Optional key for idempotent requests
            
        Returns:
            Tuple of (reservation_id, expires_at)
            
        Raises:
            InsufficientInventoryError: If not enough inventory available
        """
        # Check idempotency first
        if idempotency_key:
            cached_response = self.check_idempotency(idempotency_key)
            if cached_response:
                # Parse expires_at from cached response
                expires_at = datetime.fromisoformat(cached_response["expires_at"].replace('Z', '+00:00'))
                return cached_response["reservation_id"], expires_at
        
        inventory_key = self._get_inventory_key(sku)
        
        # Execute atomic reserve script
        success = self.reserve_script(keys=[inventory_key], args=[quantity])
        
        if not success:
            # Get current inventory for error message
            available = int(self.redis.get(inventory_key) or 0)
            raise InsufficientInventoryError(available)
        
        # Create reservation
        reservation_id = f"rsv_{uuid.uuid4().hex[:12]}"
        reservation_key = self._get_reservation_key(reservation_id)
        
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(seconds=settings.RESERVATION_TTL_SECONDS)
        
        reservation_data = ReservationData(
            user_id=user_id,
            sku=sku,
            quantity=quantity,
            created_at=created_at
        )
        
        # Store reservation without TTL (persistence handled by worker)
        self.redis.set(
            reservation_key,
            reservation_data.model_dump_json()
        )
        
        # Add to expiry tracking (sorted set by timestamp)
        self.redis.zadd(
            "expiring_reservations",
            {reservation_id: expires_at.timestamp()}
        )
        
        logger.info(
            f"Reserved {quantity} units of {sku} for user {user_id}. "
            f"Reservation: {reservation_id}, Expires: {expires_at}"
        )
        
        # Cache response for idempotency
        if idempotency_key:
            response = {
                "reservation_id": reservation_id,
                "sku": sku,
                "quantity": quantity,
                "expires_at": expires_at.isoformat() + 'Z',
                "ttl_seconds": settings.RESERVATION_TTL_SECONDS
            }
            self.redis.setex(
                self._get_idempotency_key(idempotency_key),
                settings.IDEMPOTENCY_CACHE_TTL_SECONDS,
                json.dumps(response)
            )
        
        return reservation_id, expires_at
    
    def get_reservation(self, reservation_id: str) -> Optional[ReservationData]:
        """
        Get reservation data.
        
        Args:
            reservation_id: Reservation ID
            
        Returns:
            ReservationData if exists, None otherwise
        """
        reservation_key = self._get_reservation_key(reservation_id)
        data = self.redis.get(reservation_key)
        
        if not data:
            return None
        
        return ReservationData.model_validate_json(data)
    
    def confirm_reservation(self, reservation_id: str, user_id: str, grace_period_seconds: int = 5) -> ReservationData:
        """
        Confirm and delete reservation atomically.
        
        Args:
            reservation_id: Reservation to confirm
            user_id: User confirming (for ownership validation)
            grace_period_seconds: Safety buffer for network latency
            
        Returns:
            ReservationData of confirmed reservation
            
        Raises:
            ValueError: If reservation not found or doesn't belong to user
        """
        reservation_key = self._get_reservation_key(reservation_id)
        
        # Use WATCH/MULTI/EXEC for optimistic locking
        pipe = self.redis.pipeline()
        
        try:
            pipe.watch(reservation_key)
            pipe.watch("expiring_reservations")
            
            # Get reservation
            data = pipe.get(reservation_key)
            if not data:
                raise ValueError("Reservation not found")
                
            # Check expiration explicitly (since we removed key TTL)
            expiry_score = pipe.zscore("expiring_reservations", reservation_id)
            if not expiry_score:
                 # It might be missing if processed by worker already
                 raise ValueError("Reservation expired or invalid")
            
            # Apply grace period: strict expiry is score < now
            # With grace period: expiry is score + grace < now
            # So if (score + grace) > now, it is valid.
            import time
            current_timestamp = time.time()
            if current_timestamp > (expiry_score + grace_period_seconds):
                raise ValueError("Reservation expired")
            
            reservation = ReservationData.model_validate_json(data)
            
            # Validate ownership
            if reservation.user_id != user_id:
                raise ValueError("This reservation belongs to another user")
            
            # Start transaction
            pipe.multi()
            pipe.delete(reservation_key)
            pipe.zrem("expiring_reservations", reservation_id)
            pipe.execute()
            
            logger.info(f"Confirmed reservation {reservation_id} for user {user_id}")
            return reservation
            
        except Exception as e:
            pipe.reset()
            raise e
    
    def cancel_reservation(self, reservation_id: str, user_id: str) -> bool:
        """
        Cancel a reservation manually (user initiated).
        
        Args:
            reservation_id: Reservation to cancel
            user_id: User canceling (for ownership validation)
            
        Returns:
            True if canceled, False if already gone
            
        Raises:
            ValueError: If reservation belongs to another user
        """
        reservation_key = self._get_reservation_key(reservation_id)
        
        # Get reservation data to validate ownership
        data = self.redis.get(reservation_key)
        if not data:
            return False
            
        reservation = ReservationData.model_validate_json(data)
        
        if reservation.user_id != user_id:
            raise ValueError("This reservation belongs to another user")
            
        # Re-use existing release logic
        return self.release_reservation(reservation_id)

    def release_reservation(self, reservation_id: str) -> bool:
        """
        Release expired reservation and restore inventory.
        
        Args:
            reservation_id: Reservation to release
            
        Returns:
            True if released, False if already gone
        """
        reservation_key = self._get_reservation_key(reservation_id)
        
        # Get reservation data
        data = self.redis.get(reservation_key)
        if not data:
            # Already released or confirmed
            self.redis.zrem("expiring_reservations", reservation_id)
            return False
        
        reservation = ReservationData.model_validate_json(data)
        
        # Restore inventory atomically
        inventory_key = self._get_inventory_key(reservation.sku)
        self.restore_script(keys=[inventory_key], args=[reservation.quantity])
        
        # Delete reservation
        self.redis.delete(reservation_key)
        self.redis.zrem("expiring_reservations", reservation_id)
        
        logger.info(
            f"Released expired/canceled reservation {reservation_id}. "
            f"Restored {reservation.quantity} units of {reservation.sku}"
        )
        
        return True
    
    def get_inventory_status(self, sku: str) -> dict:
        """
        Get current inventory status.
        
        Args:
            sku: Product SKU
            
        Returns:
            Dictionary with available, reserved, and total counts
        """
        inventory_key = self._get_inventory_key(sku)
        available = int(self.redis.get(inventory_key) or 0)
        
        # Count active reservations for this SKU
        # (This is approximate as we'd need to iterate all reservations)
        # For production, maintain a separate counter
        
        return {
            "sku": sku,
            "available": available,
            "reserved": 0,  # Placeholder - would need separate tracking
            "total": available
        }
    
    def set_inventory(self, sku: str, quantity: int):
        """
        Set initial inventory for a SKU.
        
        Args:
            sku: Product SKU
            quantity: Initial quantity
        """
        inventory_key = self._get_inventory_key(sku)
        self.redis.set(inventory_key, quantity)
        logger.info(f"Set inventory for {sku}: {quantity} units")
