from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.users.router import router as users_router
from app.redis.client import redis_client
from app.products.router import router as products_router
from elasticsearch import AsyncElasticsearch
from app.config import settings
from app.elasticsearch.router import router as el_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.el_cl = AsyncElasticsearch(hosts=f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}")
    app.state.scheduler = AsyncIOScheduler()
    scheduler: AsyncIOScheduler = app.state.scheduler
    yield
    el_cl: AsyncElasticsearch = app.state.el_cl
    await el_cl.close()
    
app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(products_router)
app.include_router(el_router)

    
