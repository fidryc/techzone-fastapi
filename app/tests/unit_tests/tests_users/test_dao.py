import pytest
from app.users.dao import UserDao


@pytest.fixture(scope="function")
async def user_dao(session):
    return UserDao(session)


@pytest.mark.dao
@pytest.mark.parametrize("user_id, correct_email", [(1, "admin@shop.com")])
async def test_dao(user_dao: UserDao, user_id, correct_email):
    assert (await user_dao.find_by_filter_one(user_id=user_id)).email == correct_email
