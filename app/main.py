from contextlib import asynccontextmanager
from sqladmin import Admin
from app.admin.middleware import check_admin
from app.middleware import check_time
from app.users.router import router as users_router
from app.redis.client import REDIS_URL, redis_client
from app.products.router import router as products_router
from elasticsearch import AsyncElasticsearch, Elasticsearch
from app.config import settings
from app.elasticsearch.router import router as el_router
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from app.orders.router import router as orders_router
from app.redis.router import router as redis_router
from app.stores.router import router as store_router
from app.logger import logger
from app.database import engine
from app.admin.utils import get_admin_views
from app.admin.middleware import check_admin
from app.elasticsearch.config import ELASTICSEARCH_URL
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug('App start')
    app.state.el_cl = AsyncElasticsearch(hosts=ELASTICSEARCH_URL)
    app.state.el_cl_sync = Elasticsearch(hosts=ELASTICSEARCH_URL)
    redis = aioredis.from_url(REDIS_URL)
    app.state.redis_client = redis
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    yield
    el_cl: AsyncElasticsearch = app.state.el_cl
    await el_cl.close()
    logger.debug('App close')
    
app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(products_router)
app.include_router(el_router)
app.include_router(orders_router)
app.include_router(redis_router)
app.include_router(store_router)

admin = Admin(app, engine)
views = get_admin_views()
for view in views:
    admin.add_view(view)

app.middleware('http')(check_time)
app.middleware('http')(check_admin)