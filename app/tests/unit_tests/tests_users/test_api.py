from httpx import AsyncClient
import pytest
from app.config import settings

@pytest.mark.api
@pytest.mark.parametrize(
    'email, pwd, status_code',
    [
        ('admin@shop.com', 'admin123', 200),
        ('admin@shop.com', 'fake_pwd', 401),
        ('fake@shop.com', 'fake_pwd', 401)
    ]
)
async def test_login_with_email(ac: AsyncClient, email, pwd, status_code):
    response = await ac.post(url='/users/login_with_email', json={'email': email, 'password': pwd})
    assert response.status_code == status_code


@pytest.mark.api
@pytest.mark.parametrize(
    'number, pwd, status_code',
    [
        ('+79991234567', 'admin123', 200),
        ('+79992345678', 'fake_pwd', 401),
        ('+792345678', 'fake_pwd', 401)
    ]
)
async def test_login_with_number(ac: AsyncClient, number, pwd, status_code):
    response = await ac.post(url='/users/login_with_number', json={'number': number, 'password': pwd})
    assert response.status_code == status_code


@pytest.mark.api
async def test_logout(authenticated_ac: AsyncClient):
    assert authenticated_ac.cookies[settings.JWT_ACCESS_COOKIE_NAME]
    await authenticated_ac.post('/users/logout')
    assert not authenticated_ac.cookies.get(settings.JWT_ACCESS_COOKIE_NAME, False)
    

@pytest.mark.api
async def test_delete_user(clean_authenticated_ac: AsyncClient):
    res = await clean_authenticated_ac.post('/users/delete_user')
    assert res.status_code == 200