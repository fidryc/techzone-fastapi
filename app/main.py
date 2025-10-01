from contextlib import asynccontextmanager
from redis.asyncio import Redis
from fastapi import FastAPI, Request
from app.users.router import router as users_router
from app.redis.client import redis_client
from app.products.router import router as products_router
from elasticsearch import AsyncElasticsearch, Elasticsearch
from app.config import settings
from app.elasticsearch.router import router as el_router
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from app.orders.router import router as orders_router
from app.logger import logger
from datetime import datetime, timezone

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.el_cl = AsyncElasticsearch(hosts=f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}")
    app.state.el_cl_sync = Elasticsearch(hosts=f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}")
    redis = aioredis.from_url(f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}')
    app.state.redis_client = redis
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    yield
    el_cl: AsyncElasticsearch = app.state.el_cl
    await el_cl.close()
    
app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(products_router)
app.include_router(el_router)
app.include_router(orders_router)

@app.middleware('http')
async def check_time(request: Request, call_next):
    start_time = datetime.now(timezone.utc)
    response = await call_next(request)
    logger.debug('Request execution time', extra={'total_seconds': (datetime.now(timezone.utc) - start_time).total_seconds()})
    return response

    
