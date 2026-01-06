from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings
from app.models.schemas import UserClaims

settings = get_settings()
security = HTTPBearer()


def create_access_token(user_id: str) -> str:
    """
    Create JWT access token for user.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.utcnow()
    expires = now + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    
    claims = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp())
    }
    
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify JWT token and extract user_id.
    
    Args:
        credentials: HTTP Bearer credentials from request
        
    Returns:
        user_id extracted from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        
        return user_id
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


# Dependency for routes that require authentication
async def get_current_user(user_id: str = Depends(verify_token)) -> str:
    """Dependency to get current authenticated user."""
    return user_id
