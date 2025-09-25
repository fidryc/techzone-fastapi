from typing import Annotated
from aioredis import Redis
from fastapi import Depends, Request, Response
from app.database import get_session
from app.orders.dao import OrderDao
from app.redis.services import RedisService
from app.users.dao import UserDao
from app.users.schema import UserSchema
from app.users.services import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionDep


async def get_user_service(session: SessionDep):
    return UserService(session)


async def get_user(request: Request, response: Response, user_service: Annotated[UserService, Depends(get_user_service)]):
    return await user_service.get_user_from_token(request, response)


CurrentUserDep = Annotated[UserSchema, Depends(get_user)]

UserServiceDep = Annotated[UserService, Depends(get_user_service)]

async def get_user_dao(session: SessionDep) -> UserDao:
    return UserDao(session)


async def get_order_dao(session: SessionDep) -> OrderDao:
    return OrderDao(session)
