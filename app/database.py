from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.config import settings

DATABASE_URL = f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
DATABASE_URL_SYNC = f'postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'

engine = create_async_engine(DATABASE_URL)
engine_sync = create_engine(DATABASE_URL_SYNC)

session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

session_maker_sync = sessionmaker(engine_sync, class_=Session, expire_on_commit=False)

async def get_session():
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
def get_session_sync():
    with session_maker_sync() as session:
        try:
            yield session
        finally:
            session.close()
            
class Base(DeclarativeBase):
    pass