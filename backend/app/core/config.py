from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Smart Inventory Reservation System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DECODE_RESPONSES: bool = True
    
    # PostgreSQL
    DATABASE_URL: str = "postgresql://flexype:hackathon2026@localhost:5432/inventory_system"
    
    # JWT Authentication
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 15
    
    # Business Logic
    RESERVATION_TTL_SECONDS: int = 300  # 5 minutes
    MAX_QUANTITY_PER_RESERVE: int = 5
    MIN_QUANTITY_PER_RESERVE: int = 1
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_IP_MINUTE: int = 100
    
    # Idempotency
    IDEMPOTENCY_CACHE_TTL_SECONDS: int = 310  # Slightly longer than reservation TTL
    
    # Worker
    EXPIRY_CHECK_INTERVAL_SECONDS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
