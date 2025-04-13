from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis.asyncio as redis

from app.core.config import settings

# Use Redis for distributed rate limiting if REDIS_URL is set
if settings.REDIS_URL:
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
else:
    # Fallback to in-memory limiter (not suitable for multi-process/multi-instance deployments)
    limiter = Limiter(key_func=get_remote_address)

# You can add custom states or configurations to the limiter if needed
# e.g., app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
