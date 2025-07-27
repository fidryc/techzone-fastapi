from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.config import settings

DATABASE_URL = f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'

engine = create_async_engine(DATABASE_URL)

session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with session_maker() as session:
        yield session

class Base(DeclarativeBase):
    pass