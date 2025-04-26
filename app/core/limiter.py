from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import logging

from app.core.config import settings

# Use Redis for distributed rate limiting if REDIS_URL is set
if settings.REDIS_URL:
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
else:
    # Fallback to in-memory limiter (not suitable for multi-process/multi-instance deployments)
    limiter = Limiter(key_func=get_remote_address)

# Handler for rate limit exceeded errors
async def _rate_limit_exceeded_handler(request, exc):
    """Handler for rate limit exceeded errors"""
    logging.warning(f"Rate limit exceeded: {request.client.host} - {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "limit": str(exc.detail) if hasattr(exc, "detail") else "Rate limit exceeded"
        }
    )
