from functools import wraps
from time import time
from fastapi import HTTPException, Request
from app.core.redis_client import get_redis_client
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def rate_limit(max_requests: int = None, window_seconds: int = 60):
    """
    Rate limiting decorator using Redis.
    
    Args:
        max_requests: Maximum requests allowed in window (default from settings)
        window_seconds: Time window in seconds (default 60)
    """
    if max_requests is None:
        max_requests = settings.RATE_LIMIT_PER_MINUTE
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user_id from kwargs
            request: Request = kwargs.get('request')
            user_id: str = kwargs.get('current_user')
            
            if not request or not user_id:
                # If no request or user, skip rate limiting
                return await func(*args, **kwargs)
            
            redis = get_redis_client()
            
            # Create rate limit key
            endpoint = request.url.path
            rate_key = f"ratelimit:{user_id}:{endpoint}"
            
            # Get current count
            current = redis.get(rate_key)
            
            if current is None:
                # First request in window
                pipe = redis.pipeline()
                pipe.setex(rate_key, window_seconds, 1)
                pipe.execute()
                
            else:
                current_count = int(current)
                
                if current_count >= max_requests:
                    # Rate limit exceeded
                    ttl = redis.ttl(rate_key)
                    logger.warning(
                        f"Rate limit exceeded for user {user_id} on {endpoint}. "
                        f"Count: {current_count}/{max_requests}"
                    )
                    
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "type": "https://api.flexype.com/errors/rate-limit",
                            "title": "Rate limit exceeded",
                            "status": 429,
                            "retry_after": ttl if ttl > 0 else window_seconds,
                            "detail": f"Try again in {ttl if ttl > 0 else window_seconds} seconds"
                        }
                    )
                
                # Increment counter
                redis.incr(rate_key)
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class IPRateLimiter:
    """IP-based rate limiter as fallback."""
    
    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_IP_MINUTE
        self.window_seconds = window_seconds
        self.redis = get_redis_client()
    
    def check_rate_limit(self, ip_address: str) -> bool:
        """
        Check if IP is within rate limit.
        
        Args:
            ip_address: Client IP
            
        Returns:
            True if allowed, False if rate limited
        """
        rate_key = f"ratelimit:ip:{ip_address}"
        
        current = self.redis.get(rate_key)
        
        if current is None:
            self.redis.setex(rate_key, self.window_seconds, 1)
            return True
        
        current_count = int(current)
        
        if current_count >= self.max_requests:
            return False
        
        self.redis.incr(rate_key)
        return True
