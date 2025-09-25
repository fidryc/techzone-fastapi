from typing import Annotated
from aioredis import Redis
from fastapi import Depends, Request, Response
from app.database import get_session
from app.orders.dao import OrderDao
from app.redis.services import RedisService



def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client


RedisClientDep = Annotated[Redis, Depends(get_redis_client)]


async def get_redis_service(redis_client: RedisClientDep):
    return RedisService(redis_client)


RedisServiceDep = Annotated[RedisService, Depends(get_redis_service)]