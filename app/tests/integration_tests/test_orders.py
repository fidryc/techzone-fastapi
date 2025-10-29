import json
from httpx import AsyncClient
import pytest
from app.config import settings
from app.tests.conftest import session

@pytest.mark.parametrize(
    'product_id, st_code_add_basket, store_id, st_code_create_order, count_orders',
    [
        (-1, 422, 1, 400, 0),
        (1, 200, 1, 200, 1),
        (-1, 422, 1, 400, 1),
        (1, 200, 1, 200, 2),
        (1, 200, 1, 200, 3),
        (1, 200, 1, 200, 4),
        (1, 200, 1, 200, 5),
        (1, 200, 1, 409, 5),
    ]
)
async def test_order_pickup(authenticated_ac: AsyncClient, product_id, st_code_add_basket, store_id, st_code_create_order, count_orders):
    """Тестирование добавление в корзину - создание заказа"""
    response_basket = await authenticated_ac.post('/orders/add_to_basket', params={'product_id': product_id})
    assert response_basket.status_code == st_code_add_basket
    response_create_order = await authenticated_ac.post('/orders/create_order_pickup', json={'store_id': store_id})
    assert response_create_order.status_code == st_code_create_order
    rp_orders = await authenticated_ac.get('/orders/get_orders')
    assert len(rp_orders.json()) == count_orders

