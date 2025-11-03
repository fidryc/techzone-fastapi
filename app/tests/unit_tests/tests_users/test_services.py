import pytest
from app.orders.dao import OrderDao
from app.redis.services import RedisService
from app.users.dao import RefreshTokenBLDao, UserDao
from app.users.models import RefreshTokenBL
from app.users.services import RefreshTokenBLService, UserService


@pytest.fixture(scope="function")
def user_service(ac, session):
    user_dao = UserDao()
    order_dao = OrderDao()
    rf_bl_service = RefreshTokenBLService(
        session=session, refresh_token_bl_dao=RefreshTokenBLDao(session)
    )
    redis_service = RedisService(ac.state.redis_client)
    return UserService(user_dao, order_dao, rf_bl_service, redis_service)
