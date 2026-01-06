import redis
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30
        )
    
    return _redis_client


def close_redis_client():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None


# Lua script for atomic inventory check and decrement
RESERVE_INVENTORY_SCRIPT = """
local inventory_key = KEYS[1]
local quantity = tonumber(ARGV[1])

-- Get current inventory
local available = tonumber(redis.call('GET', inventory_key) or 0)

-- Check if enough inventory available
if available >= quantity then
    -- Decrement inventory
    redis.call('DECRBY', inventory_key, quantity)
    return 1
else
    -- Not enough inventory
    return 0
end
"""

# Lua script for atomic inventory restoration (on expiry)
RESTORE_INVENTORY_SCRIPT = """
local inventory_key = KEYS[1]
local quantity = tonumber(ARGV[1])

redis.call('INCRBY', inventory_key, quantity)
return 1
"""
