from typing import Annotated
from fastapi import Depends, Request, Response
from app.orders.depends import OrderDaoDep
from app.redis.depends import RedisServiceDep
from app.users.dao import UserDao
from app.users.schema import UserSchema
from app.users.services import UserService
from app.database import SessionDep


async def get_user_dao(session: SessionDep) -> UserDao:
    return UserDao(session)

UserDaoDep = Annotated[UserDao, Depends(get_user_dao)]


async def get_user_service(user_dao: UserDaoDep, order_dao: OrderDaoDep, redis_service: RedisServiceDep, session: SessionDep):
    return UserService(user_dao, order_dao, redis_service, session)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_user(request: Request, response: Response, user_service: UserServiceDep):
    return await user_service.get_user_from_token(request, response)

CurrentUserDep = Annotated[UserSchema, Depends(get_user)]
