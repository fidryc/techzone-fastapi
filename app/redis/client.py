from redis.asyncio import Redis
from app.config import settings

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)

REDIS_URL = settings.REDIS_URL
