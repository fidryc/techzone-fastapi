from app.database import session_maker
from sqlalchemy import insert, values, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.logger import logger
from fastapi import HTTPException
from app.logger import create_msg_db_error


class Pass:
    pass


class BaseDao:
    model = Pass

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, **data):
        query = insert(self.model).values(**data)
        try:
            await self.session.execute(query)
            logger.debug(f"Succefuly add in {self.model}")
        except SQLAlchemyError:
            msg = create_msg_db_error(f"Failed add in {self.model}")
            logger.error(msg, extra=data, exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Ошибка при добавлении данных в {self.model}"
            )

    async def find_by_id(self, id):
        query = select(self.model).filter_by(id=id)
        try:
            obj = await self.session.execute(query)
            logger.debug(f"Succefuly find by id in {self.model}")
            return obj.scalar_one_or_none()
        except SQLAlchemyError:
            msg = create_msg_db_error(f"Failed find by id in {self.model}")
            logger.error(msg, extra={"id": id}, exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Ошибка при поиске строки по id в {self.model}"
            )

    async def find_by_filter(self, **filters):
        query = select(self.model).filter_by(**filters)
        try:
            obj = await self.session.execute(query)
            logger.debug(f"Succefuly find by filter in {self.model}")
            return obj.scalars().all()
        except SQLAlchemyError as e:
            msg = create_msg_db_error(f"Failed find by filter in {self.model}")
            logger.error(msg, extra=filters, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при поиске строк по фильтрам в {self.model}",
            ) from e

    async def find_by_filter_one(self, **filters):
        query = select(self.model).filter_by(**filters)
        try:
            obj = await self.session.execute(query)
            logger.debug(f"Succefuly find by filter a row in {self.model}")
            return obj.scalar_one_or_none()
        except SQLAlchemyError:
            msg = create_msg_db_error(f"Failed find by filter a row in {self.model}")
            logger.error(msg, extra=filters, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при поиске строки по фильтру в {self.model}",
            )

    async def all(self):
        query = select(self.model)
        try:
            obj = await self.session.execute(query)
            return obj.scalars().all()
        except SQLAlchemyError:
            msg = create_msg_db_error(f"Failed find by filter a row in {self.model}")
            logger.error(msg, extra={"model": self.model}, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при поиске строки по фильтру в {self.model}",
            )


# Синхронный вариант для celery
class BaseSyncDao:
    model = Pass

    def __init__(self, session: Session):
        self.session = session

    def all(self):
        query = select(self.model)
        obj = self.session.execute(query)
        return obj.scalars().all()
