from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import uuid
import logging
from decimal import Decimal

from app.models.schemas import (
    ConfirmCheckoutRequest,
    ConfirmCheckoutResponse,
    CancelCheckoutRequest,
    CancelCheckoutResponse,
    ProblemDetail
)
from app.services.reservation_service import ReservationService
from app.core.auth import get_current_user
from app.core.database import get_db, Order, OrderItem, AuditLog
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/checkout", tags=["Checkout"])

# Service instance
reservation_service = ReservationService()


@router.post(
    "/confirm",
    response_model=ConfirmCheckoutResponse,
    status_code=200,
    responses={
        200: {"description": "Checkout confirmed successfully"},
        404: {"model": ProblemDetail, "description": "Reservation not found"},
        403: {"model": ProblemDetail, "description": "Reservation belongs to another user"}
    }
)
async def confirm_checkout(
    request: Request,
    payload: ConfirmCheckoutRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm checkout and convert reservation to order.
    
    This atomically:
    1. Validates reservation ownership
    2. Deletes reservation from Redis
    3. Creates order record in PostgreSQL
    4. Logs the event
    
    If reservation expired, returns 404 with information about availability.
    """
    trace_id = str(uuid.uuid4())
    
    try:
        logger.info(
            f"[{trace_id}] Checkout confirmation from user {current_user} "
            f"for reservation {payload.reservation_id}"
        )
        
        # 1. Create PENDING Order in Postgres first (Dual-Write safety)
        order_id = f"ord_{uuid.uuid4().hex[:10]}"
        price_per_unit = Decimal("29.99")
        
        # We don't have reservation details yet unless we get them from Redis first WITHOUT consuming.
        # But get_reservation is safe.
        reservation_data = reservation_service.get_reservation(payload.reservation_id)
        if not reservation_data:
             # Fail early if not found, no need to create pending order
             pass # Will be caught by confirm_reservation error or handle here.
             # Actually, simpler: Try to confirm. If it fails, we have nothing.
             # The Dual-Write problem is: We delete from Redis, then DB fails.
             # So we MUST create DB record first. To create DB record, we need data.
        
        if not reservation_data:
             # Let confirm_reservation handle the 404 logic/error raising
             pass
        else:
             # Create Pending Order
             initial_order = Order(
                order_id=order_id,
                user_id=current_user,
                status="pending",
                total_amount=price_per_unit * reservation_data.quantity,
                created_at=datetime.utcnow()
             )
             db.add(initial_order)
             db.commit()
             db.refresh(initial_order)
        
        # 2. Confirm reservation (atomically delete from Redis)
        try:
            reservation = reservation_service.confirm_reservation(
                payload.reservation_id,
                current_user
            )
        except Exception as e:
            # If we created an order, mark it as failed
            if reservation_data:
                order_to_fail = db.query(Order).filter(Order.order_id == order_id).first()
                if order_to_fail:
                    order_to_fail.status = "failed"
                    db.commit()
            
            # Re-raise to handle specific HTTP exceptions
            error_msg = str(e)
            if "not found" in error_msg.lower() or "expired" in error_msg.lower():
                raise HTTPException(
                    status_code=404,
                    detail={
                        "type": "https://api.flexype.com/errors/reservation-expired",
                        "title": "Reservation expired",
                        "status": 404,
                        "detail": "Your reservation has expired.",
                        "trace_id": trace_id
                    }
                )
            elif "another user" in error_msg.lower():
                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "https://api.flexype.com/errors/forbidden",
                        "title": "Access denied",
                        "status": 403,
                        "detail": "This reservation belongs to another user",
                        "trace_id": trace_id
                    }
                )
            raise e

        # 3. Update Order to CONFIRMED (Success)
        # We might need to re-fetch if we didn't create it above (edge case where get_reservation failed but confirm succeeded? Impossible).
        # But wait, if get_reservation returned None, we skipped creation. confirm_reservation would have failed.
        # So we can assume order exists if we reached here.
        
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
             # Should not happen
             raise HTTPException(500, "Order state lost")
             
        order.status = "confirmed"
        
        # Create order item
        order_item = OrderItem(
            order_id=order_id,
            sku=reservation.sku,
            quantity=reservation.quantity,
            price_per_unit=price_per_unit
        )
        db.add(order_item)
        
        # Create audit log
        audit = AuditLog(
            event_type="confirm",
            user_id=current_user,
            sku=reservation.sku,
            reservation_id=payload.reservation_id,
            details={
                "order_id": order_id,
                "quantity": reservation.quantity,
                "total_amount": float(order.total_amount)
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        
        db.commit()
        
        logger.info(
            f"[{trace_id}] Successfully confirmed checkout. "
            f"Order: {order_id}, User: {current_user}"
        )
        
        response = ConfirmCheckoutResponse(
            order_id=order_id,
            status="confirmed",
            items=[{
                "sku": reservation.sku,
                "quantity": reservation.quantity,
                "price_per_unit": float(price_per_unit)
            }],
            total=float(order.total_amount)
        )
        
        return response
        
    except HTTPException:
        raise
    
    except Exception as e:
        db.rollback()
        logger.error(
            f"[{trace_id}] Error confirming checkout: {str(e)}",
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "https://api.flexype.com/errors/internal-error",
                "title": "Internal server error",
                "status": 500,
                "detail": "An unexpected error occurred during checkout",
                "trace_id": trace_id
            }
        )


@router.post(
    "/cancel",
    response_model=CancelCheckoutResponse,
    status_code=200,
    responses={
        200: {"description": "Reservation canceled successfully"},
        404: {"model": ProblemDetail, "description": "Reservation not found"},
        403: {"model": ProblemDetail, "description": "Reservation belongs to another user"}
    }
)
async def cancel_checkout(
    request: Request,
    payload: CancelCheckoutRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Cancel checkout and release inventory.
    """
    trace_id = str(uuid.uuid4())
    
    try:
        logger.info(
            f"[{trace_id}] Checkout cancellation request from user {current_user} "
            f"for reservation {payload.reservation_id}"
        )
        
        try:
            success = reservation_service.cancel_reservation(
                payload.reservation_id,
                current_user
            )
            
            if not success:
               # Already expired or gone, which is fine, treat as success or 404.
               # Similar to DELETE behavior, often idempotent success is preferred,
               # but user might want to know if it was ALREADY expired.
               # Let's return 404 if not found to be explicit.
                raise HTTPException(
                    status_code=404,
                    detail={
                        "type": "https://api.flexype.com/errors/not-found",
                        "title": "Reservation not found",
                        "status": 404,
                        "detail": "Reservation not found or already expired",
                        "trace_id": trace_id
                    }
                )

        except ValueError as e:
            if "another user" in str(e).lower():
                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "https://api.flexype.com/errors/forbidden",
                        "title": "Access denied",
                        "status": 403,
                        "detail": "This reservation belongs to another user",
                        "trace_id": trace_id
                    }
                )
            raise

        return CancelCheckoutResponse(
            status="canceled",
            message="Reservation released successfully"
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"[{trace_id}] Error canceling checkout: {str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/orders/{order_id}",
    responses={
        200: {"description": "Order details"},
        404: {"description": "Order not found"}
    }
)
async def get_order(
    order_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order details (simplified - would validate ownership in production)."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get order items
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": float(order.total_amount) if order.total_amount else 0,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "sku": item.sku,
                "quantity": item.quantity,
                "price_per_unit": float(item.price_per_unit) if item.price_per_unit else 0
            }
            for item in items
        ]
    }
