import redis.asyncio as redis
from app.core.config import settings

# Initialize the async Redis client
# We use decode_responses=True to get strings back instead of bytes
redis_client = redis.from_url(settings.redis_url, decode_responses=True)
