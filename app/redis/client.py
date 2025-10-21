from redis.asyncio import Redis
from app.config import settings

if settings.MODE == 'DEV':
    REDIS_HOST = settings.REDIS_HOST
elif settings.MODE == 'PROD':
    REDIS_HOST = settings.REDIS_HOST_PROD
  
redis_client = Redis(
    host=REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

REDIS_URL = f'redis://{REDIS_HOST}:{settings.REDIS_PORT}'