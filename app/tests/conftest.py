import asyncio
import aioredis
from elasticsearch import AsyncElasticsearch, Elasticsearch
from fastapi_cache import FastAPICache
import pytest
from sqlalchemy import insert
from app.elasticsearch.config import ELASTICSEARCH_URL
from app.orders import models
from app.users import models
from app.stores import models
from app.products import models
from app.database import Base
from app.config import settings
from app.database import engine, session_maker
from app.tests.data_for_test.data_for_init_db import INSERT_TABLES
from app.tests.utils import reset_sequences
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app as fastapi_app
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis


@pytest.fixture(scope='session', autouse=True)
async def prepare_db():
    assert settings.MODE == 'TEST'
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with session_maker() as session:
        for table_name, insert_datas in INSERT_TABLES:
            table = Base.metadata.tables[table_name]
            query = insert(table).values(insert_datas)
            await session.execute(query)
        await session.commit()
        
    async with engine.begin() as conn:
        await reset_sequences(conn)
            
        
@pytest.fixture(scope="session")
def event_loop():
    """Современный способ для session scope"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='function')
async def session():
    async with session_maker() as ses:
        yield ses
        
        
@pytest.fixture(scope='function')
async def ac():
    fastapi_app.state.el_cl = AsyncElasticsearch(hosts=ELASTICSEARCH_URL)
    fastapi_app.state.el_cl_sync = Elasticsearch(hosts=ELASTICSEARCH_URL)
    redis = aioredis.from_url(settings.REDIS_URL)
    fastapi_app.state.redis_client = redis
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url='http://test') as app_client:
        yield app_client
        
    el_cl: AsyncElasticsearch = fastapi_app.state.el_cl
    await el_cl.close()
        
        
@pytest.fixture(scope='function')
async def authenticated_ac():
    fastapi_app.state.el_cl = AsyncElasticsearch(hosts=ELASTICSEARCH_URL)
    fastapi_app.state.el_cl_sync = Elasticsearch(hosts=ELASTICSEARCH_URL)
    redis = aioredis.from_url(settings.REDIS_URL)
    fastapi_app.state.redis_client = redis
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url='http://test') as app_client:
        await app_client.post('/users/login_with_email', json={'email': 'admin@shop.com', 'password': 'admin123'})
        assert app_client.cookies[settings.JWT_ACCESS_COOKIE_NAME]
        yield app_client
        
    el_cl: AsyncElasticsearch = fastapi_app.state.el_cl
    await el_cl.close()
    
    
@pytest.fixture(scope='function')
async def clean_authenticated_ac():
    fastapi_app.state.el_cl = AsyncElasticsearch(hosts=ELASTICSEARCH_URL)
    fastapi_app.state.el_cl_sync = Elasticsearch(hosts=ELASTICSEARCH_URL)
    redis = aioredis.from_url(settings.REDIS_URL)
    fastapi_app.state.redis_client = redis
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url='http://test') as app_client:
        await app_client.post('/users/login_with_email', json={'email': 'clear@gmail.com', 'password': 'clear123'})
        assert app_client.cookies[settings.JWT_ACCESS_COOKIE_NAME]
        yield app_client
        
    el_cl: AsyncElasticsearch = fastapi_app.state.el_cl
    await el_cl.close()
