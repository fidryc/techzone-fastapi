from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.config import settings
from app.logger import logger


if settings.MODE == 'DEV':
    DATABASE_URL = f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
    DATABASE_URL_SYNC = f'postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
elif settings.MODE == 'PROD':
    DATABASE_URL = f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST_PROD}:{settings.DB_PORT}/{settings.DB_NAME}'
    DATABASE_URL_SYNC = f'postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST_PROD}:{settings.DB_PORT}/{settings.DB_NAME}'
    
    
engine = create_async_engine(DATABASE_URL)
engine_sync = create_engine(DATABASE_URL_SYNC)

session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

session_maker_sync = sessionmaker(engine_sync, class_=Session, expire_on_commit=False)

async def get_session():
    async with session_maker() as session:
        try:
            logger.debug(msg='Open session')
            yield session
        finally:
            logger.debug(msg='Close session')
            await session.close()
            
SessionDep = Annotated[AsyncSession, Depends(get_session)]
            
            
def get_session_sync():
    with session_maker_sync() as session:
        try:
            yield session
        finally:
            session.close()
            
            
class Base(DeclarativeBase):
    def __repr__(self):
        return self.__tablename__
    
    def _find(self):
        for key in self.__dict__:
            if key.endswith('id') and key.startswith(self.__class__.__name__.lower()):
                return key
        else:
            return ''
            
    def __str__(self):
        id_key = self._find()
        if id_key:
            return f'{self.__class__.__name__} {getattr(self, id_key)}'
        else:
            return '{self.__class__.__name__}'
    
    def __format__(self, format_spec: str) -> str:
        return format(self.__tablename__, format_spec)