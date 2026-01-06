from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# Request Models
class ReserveInventoryRequest(BaseModel):
    """Request model for reserving inventory."""
    sku: str = Field(..., min_length=1, max_length=50, pattern=r'^[A-Za-z0-9\-]+$')
    quantity: int = Field(..., ge=1, le=5)
    
    @validator('sku')
    def validate_sku(cls, v):
        """Validate SKU format."""
        if not v or not v.strip():
            raise ValueError('SKU cannot be empty')
        return v.strip().upper()


class ConfirmCheckoutRequest(BaseModel):
    """Request model for confirming checkout."""
    reservation_id: str = Field(..., min_length=1, max_length=20)


class CancelCheckoutRequest(BaseModel):
    """Request model for canceling checkout."""
    reservation_id: str = Field(..., min_length=1, max_length=20)


# Response Models
class ReserveInventoryResponse(BaseModel):
    """Response model for successful inventory reservation."""
    reservation_id: str
    sku: str
    quantity: int
    expires_at: str  # ISO 8601 timestamp
    ttl_seconds: int


class ConfirmCheckoutResponse(BaseModel):
    """Response model for successful checkout confirmation."""
    order_id: str
    status: str
    items: List[dict]
    total: float


class CancelCheckoutResponse(BaseModel):
    """Response model for successful checkout cancellation."""
    status: str
    message: str


class InventoryStatusResponse(BaseModel):
    """Response model for inventory status."""
    sku: str
    available: int
    reserved: int
    total: int


# Error Models (RFC 7807)
class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: str
    message: str


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details for HTTP APIs."""
    type: str
    title: str
    status: int
    detail: str
    trace_id: Optional[str] = None
    errors: Optional[List[ErrorDetail]] = None
    available: Optional[int] = None  # For insufficient inventory
    retry_after: Optional[int] = None  # For rate limiting


# Internal Models
class ReservationData(BaseModel):
    """Internal model for reservation data stored in Redis."""
    user_id: str
    sku: str
    quantity: int
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserClaims(BaseModel):
    """JWT token claims."""
    sub: str  # user_id
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
