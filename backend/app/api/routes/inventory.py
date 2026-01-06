from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional
from datetime import datetime
import uuid
import logging

from app.models.schemas import (
    ReserveInventoryRequest,
    ReserveInventoryResponse,
    InventoryStatusResponse,
    ProblemDetail
)
from app.services.reservation_service import ReservationService, InsufficientInventoryError
from app.core.auth import get_current_user
from app.api.middleware.rate_limiter import rate_limit
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])

# Service instance
reservation_service = ReservationService()


@router.post(
    "/reserve",
    response_model=ReserveInventoryResponse,
    status_code=201,
    responses={
        201: {"description": "Reservation created successfully"},
        400: {"model": ProblemDetail, "description": "Invalid request"},
        409: {"model": ProblemDetail, "description": "Insufficient inventory"},
        429: {"model": ProblemDetail, "description": "Rate limit exceeded"}
    }
)
@rate_limit()
async def reserve_inventory(
    request: Request,
    payload: ReserveInventoryRequest,
    current_user: str = Depends(get_current_user),
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Reserve inventory for a user.
    
    This endpoint atomically checks and decrements inventory using Redis Lua scripts
    to prevent race conditions and overselling.
    
    **Idempotency**: Include `X-Idempotency-Key` header to safely retry requests.
    
    **Rate Limit**: 10 requests per minute per user.
    """
    trace_id = str(uuid.uuid4())
    
    try:
        logger.info(
            f"[{trace_id}] Reserve request from user {current_user}: "
            f"{payload.quantity} units of {payload.sku}"
        )
        
        # Reserve inventory
        reservation_id, expires_at = reservation_service.reserve_inventory(
            sku=payload.sku,
            quantity=payload.quantity,
            user_id=current_user,
            idempotency_key=x_idempotency_key
        )
        
        response = ReserveInventoryResponse(
            reservation_id=reservation_id,
            sku=payload.sku,
            quantity=payload.quantity,
            expires_at=expires_at.isoformat() + 'Z',
            ttl_seconds=settings.RESERVATION_TTL_SECONDS
        )
        
        logger.info(
            f"[{trace_id}] Successfully reserved {payload.quantity} units of {payload.sku}. "
            f"Reservation: {reservation_id}"
        )
        
        return response
        
    except InsufficientInventoryError as e:
        logger.warning(
            f"[{trace_id}] Insufficient inventory for {payload.sku}. "
            f"Requested: {payload.quantity}, Available: {e.available}"
        )
        
        raise HTTPException(
            status_code=409,
            detail={
                "type": "https://api.flexype.com/errors/insufficient-inventory",
                "title": "Not enough items available",
                "status": 409,
                "detail": f"Requested {payload.quantity} but only {e.available} available",
                "available": e.available,
                "trace_id": trace_id
            }
        )
    
    except Exception as e:
        logger.error(f"[{trace_id}] Error reserving inventory: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "https://api.flexype.com/errors/internal-error",
                "title": "Internal server error",
                "status": 500,
                "detail": "An unexpected error occurred",
                "trace_id": trace_id
            }
        )


@router.get(
    "/{sku}",
    response_model=InventoryStatusResponse,
    responses={
        200: {"description": "Inventory status retrieved successfully"}
    }
)
async def get_inventory_status(sku: str):
    """
    Get current inventory status for a SKU.
    
    Returns available quantity and reservation information.
    """
    try:
        status = reservation_service.get_inventory_status(sku)
        return InventoryStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting inventory status for {sku}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{sku}/initialize",
    status_code=201,
    responses={
        201: {"description": "Inventory initialized successfully"}
    }
)
async def initialize_inventory(
    sku: str,
    quantity: int,
    current_user: str = Depends(get_current_user)
):
    """
    Initialize inventory for a SKU (admin only - simplified for hackathon).
    
    In production, this would require admin role verification.
    """
    try:
        reservation_service.set_inventory(sku, quantity)
        
        return {
            "message": f"Initialized {quantity} units for {sku}",
            "sku": sku,
            "quantity": quantity
        }
        
    except Exception as e:
        logger.error(f"Error initializing inventory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
