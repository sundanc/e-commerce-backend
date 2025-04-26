import json
import logging
import asyncio
from typing import Any, Optional, TypeVar, Callable
import redis.asyncio as redis
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

# Connect to Redis if URL is set
redis_client = None
if settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")

T = TypeVar('T')

async def get_cached_data(key: str) -> Optional[str]:
    """Get data from Redis cache."""
    if not redis_client:
        return None
    
    try:
        data = await redis_client.get(key)
        return data
    except Exception as e:
        logger.warning(f"Redis get error for key {key}: {e}")
        return None

async def set_cached_data(key: str, data: str, expire_seconds: int = 3600) -> bool:
    """Set data in Redis cache with expiration."""
    if not redis_client:
        return False
    
    try:
        await redis_client.set(key, data, ex=expire_seconds)
        return True
    except Exception as e:
        logger.warning(f"Redis set error for key {key}: {e}")
        return False

async def invalidate_cache(pattern: str) -> None:
    """Invalidate cache entries matching a pattern."""
    if not redis_client:
        return
    
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.debug(f"Invalidated {len(keys)} cache entries matching '{pattern}'")
    except Exception as e:
        logger.warning(f"Redis invalidation error for pattern {pattern}: {e}")

def cache_response(prefix: str, expire_seconds: int = 3600):
    """Decorator to cache API responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # For non-async endpoints, simply pass through
            if not asyncio.iscoroutinefunction(func):
                return func(*args, **kwargs)
                
            # Generate cache key from function name and arguments
            key_parts = [prefix, func.__name__]
            
            # Add sorted kwargs to ensure consistent key ordering
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if k != "db" and k != "current_user":  # Skip DB and user objects
                    key_parts.append(f"{k}:{v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await get_cached_data(cache_key)
            if cached_result:
                try:
                    return json.loads(cached_result)
                except json.JSONDecodeError:
                    # If cached data is corrupted, proceed with normal execution
                    pass
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            try:
                await set_cached_data(cache_key, json.dumps(result), expire_seconds)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not cache response: {e}")
            
            return result
        return wrapper
    return decorator
