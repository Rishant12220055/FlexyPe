from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.auth import create_access_token, get_password_hash, verify_password
from app.core.database import get_db, User
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""
    user_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Registration request model."""
    user_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str
    expires_in: int


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"}
    }
)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    try:
        # Find user
        user = db.query(User).filter(User.user_id == payload.user_id).first()
        
        if not user or not verify_password(payload.password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {payload.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        token = create_access_token(user.user_id)
        
        logger.info(f"User {payload.user_id} logged in successfully")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=900  # 15 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=201,
    responses={
        201: {"description": "Registration successful"},
        409: {"description": "User already exists"}
    }
)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user."""
    try:
        # Check if user exists
        if db.query(User).filter(User.user_id == payload.user_id).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
            
        # Create new user
        user = User(
            user_id=payload.user_id,
            password_hash=get_password_hash(payload.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        token = create_access_token(user.user_id)
        
        logger.info(f"User {payload.user_id} registered successfully")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=900  # 15 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
