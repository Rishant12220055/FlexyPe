"""
Background worker for releasing expired reservations.

This worker runs independently and periodically checks for expired reservations,
restoring inventory and cleaning up Redis keys.
"""
import time
import logging
from datetime import datetime
from app.services.reservation_service import ReservationService
from app.core.redis_client import get_redis_client
from app.core.database import SessionLocal, AuditLog
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()


def release_expired_reservations():
    """
    Check for and release expired reservations.
    
    This function:
    1. Queries sorted set for reservations expired before now
    2. For each expired reservation, restores inventory
    3. Cleans up Redis keys
    4. Logs to PostgreSQL audit table
    """
    service = ReservationService()
    redis = get_redis_client()
    db = SessionLocal()
    
    try:
        now = time.time()
        
        # Get all reservations that should have expired by now
        expired = redis.zrangebyscore("expiring_reservations", 0, now)
        
        if not expired:
            logger.debug("No expired reservations to process")
            return
        
        logger.info(f"Processing {len(expired)} expired reservations")
        
        for reservation_id in expired:
            try:
                # Get reservation data before releasing
                reservation = service.get_reservation(reservation_id)
                
                # Release reservation (restores inventory)
                released = service.release_reservation(reservation_id)
                
                if released and reservation:
                    # Log to audit table
                    audit = AuditLog(
                        event_type="expire",
                        user_id=reservation.user_id,
                        sku=reservation.sku,
                        reservation_id=reservation_id,
                        details={
                            "quantity": reservation.quantity,
                            "created_at": reservation.created_at.isoformat(),
                            "expired_at": datetime.utcnow().isoformat()
                        },
                        timestamp=datetime.utcnow()
                    )
                    db.add(audit)
                    db.commit()
                    
                    logger.info(
                        f"Released expired reservation {reservation_id}: "
                        f"{reservation.quantity} units of {reservation.sku} "
                        f"for user {reservation.user_id}"
                    )
                
            except Exception as e:
                logger.error(
                    f"Error releasing reservation {reservation_id}: {str(e)}",
                    exc_info=True
                )
                db.rollback()
        
    except Exception as e:
        logger.error(f"Error in expiry worker: {str(e)}", exc_info=True)
        db.rollback()
    
    finally:
        db.close()


def main():
    """Main worker loop."""
    logger.info(
        f"Starting expiry worker. "
        f"Check interval: {settings.EXPIRY_CHECK_INTERVAL_SECONDS}s"
    )
    
    while True:
        try:
            release_expired_reservations()
        except Exception as e:
            logger.error(f"Unhandled error in worker: {str(e)}", exc_info=True)
        
        # Sleep until next check
        time.sleep(settings.EXPIRY_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
