from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.auth import create_access_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model (simplified for hackathon)."""
    user_id: str


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str
    expires_in: int


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {"description": "Login successful"}
    }
)
async def login(payload: LoginRequest):
    """
    Simplified login endpoint for hackathon.
    
    In production, this would:
    - Validate credentials against database
    - Hash and compare passwords
    - Implement account lockout
    - Add MFA support
    
    For now, accepts any user_id and issues JWT token.
    """
    try:
        # Create JWT token
        token = create_access_token(payload.user_id)
        
        logger.info(f"User {payload.user_id} logged in")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=900  # 15 minutes
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=201,
    responses={
        201: {"description": "Registration successful"}
    }
)
async def register(payload: LoginRequest):
    """
    Simplified registration endpoint for hackathon.
    
    In production, this would:
    - Validate email format
    - Hash password with bcrypt
    - Store user in database
    - Send verification email
    
    For now, immediately issues JWT token.
    """
    try:
        # Create JWT token
        token = create_access_token(payload.user_id)
        
        logger.info(f"User {payload.user_id} registered")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=900  # 15 minutes
        )
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
