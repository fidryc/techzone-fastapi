from fastapi import Request
from fastapi.responses import JSONResponse
from app.database import session_maker
from app.orders.dao import OrderDao
from app.redis.services import RedisService
from app.users.dao import UserDao
from app.users.dao import RefreshTokenBLDao
from app.users.services import RefreshTokenBLService, UserService
from fastapi.exceptions import HTTPException

async def check_admin(request: Request, call_next):
    response = await call_next(request)
    
    if not request.url.path.startswith("/admin"):
        print(request.url.path)
        return response
    else:
        async with session_maker() as session:
            user_dao = UserDao(session)
            order_dao = OrderDao(session)
            refresh_token_bl_dao = RefreshTokenBLDao(session)
            refresh_token_bl_service = RefreshTokenBLService(session, refresh_token_bl_dao)
            redis_client = getattr(request.state, "redis_client", None)
            redis_service = RedisService(redis_client)
            
            user_service = UserService(user_dao, order_dao, refresh_token_bl_service, redis_service, session)
            try:
                await user_service.check_admin(request, response)
                print('AAAAAAAAAAAAAAAAAAAAAAAa')
                return response
            except HTTPException:
                print('BBBBBBBBBBBBBBBBBBBBBBBB')
                return JSONResponse(
                status_code=403,
                content={"detail": "У вас нет прав для входа в админ-панель"}
            )