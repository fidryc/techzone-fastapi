import json
from fastapi import HTTPException
from redis.asyncio import Redis
from app.config import settings

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

