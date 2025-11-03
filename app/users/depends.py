from typing import Annotated
from fastapi import Depends, HTTPException, Request, Response
from app.orders.depends import OrderDaoDep
from app.redis.depends import RedisServiceDep
from app.users.dao import RefreshTokenBLDao, UserDao
from app.users.schema import UserSchema
from app.users.services import RefreshTokenBLService, RegisterService, UserService
from app.database import SessionDep


async def get_refresh_token_bl_dao(session: SessionDep) -> RefreshTokenBLDao:
    return RefreshTokenBLDao(session)


RefreshTokenBLDaoDep = Annotated[RefreshTokenBLDao, Depends(get_refresh_token_bl_dao)]


async def get_refresh_token_bl_service(
    session: SessionDep, refresh_token_bl_dao: RefreshTokenBLDaoDep
) -> RefreshTokenBLService:
    return RefreshTokenBLService(session, refresh_token_bl_dao)


RefreshTokenBLServiceDep = Annotated[
    RefreshTokenBLService, Depends(get_refresh_token_bl_service)
]


async def get_user_dao(session: SessionDep) -> UserDao:
    return UserDao(session)


UserDaoDep = Annotated[UserDao, Depends(get_user_dao)]


async def get_user_service(
    user_dao: UserDaoDep,
    order_dao: OrderDaoDep,
    rf_t_bl_service: RefreshTokenBLServiceDep,
    redis_service: RedisServiceDep,
    session: SessionDep,
):
    return UserService(user_dao, order_dao, rf_t_bl_service, redis_service, session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_user(request: Request, response: Response, user_service: UserServiceDep):
    return await user_service.get_user_from_token(request, response)


CurrentUserDep = Annotated[UserSchema, Depends(get_user)]


async def get_user_extended_rights(user: CurrentUserDep):
    if user.role in ("admin", "seller"):
        return user
    raise HTTPException(403, "У вас нет прав для смены статуса заказа")


CurrentUserExtendedRightsDep = Annotated[UserSchema, Depends(get_user_extended_rights)]


async def get_register_service(
    user_dao: UserDaoDep, redis_service: RedisServiceDep, session: SessionDep
):
    return RegisterService(user_dao, redis_service, session)


RegisterServiceDep = Annotated[RegisterService, Depends(get_register_service)]
