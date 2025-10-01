from fastapi import APIRouter, Depends, Request, Response

from app.database import SessionDep, get_session
from app.orders.schema import OrderDeliveryDetailSchema, OrderPickUpDetailSchema
from app.orders.services import BasketService, OrderDeliveryService, OrderPickUpService, OrderService
from app.products.services import ProductService
from app.users.depends import CurrentUserDep
from app.users.services import UserService

router = APIRouter(
    prefix='/orders',
    tags=['Заказы']
)


@router.post('/add_to_basket')
async def add_to_basket(user: CurrentUserDep, session: SessionDep, product_id: int):
    '''Создание заказа с самовывозом со статусом new с товарами из basket'''
    basket_service = BasketService(session)
    return await basket_service.add_to_basket(product_id, user.user_id)


@router.post('/create_order_pickup')
async def create_order_pickup(user: CurrentUserDep, session: SessionDep, order_details: OrderPickUpDetailSchema):
    '''Создание заказа с самовывозом со статусом new с товарами из basket'''
    order_service = OrderPickUpService(session)
    return await order_service.create_order_pickup(user.user_id, order_details.model_dump())


@router.post('/create_order_delivery')
async def create_order_delivery(user: CurrentUserDep, session: SessionDep, order_details: OrderDeliveryDetailSchema):
    '''Создание заказа с доставкой со статусом new с товарами из basket'''
    order_service = OrderDeliveryService(session)
    return await order_service.create_order_delivery(user.user_id, order_details.model_dump())


@router.get('/get_orders')
async def get_orders(user: CurrentUserDep, session: SessionDep):
    order_service = OrderService(session)
    return await order_service.get_orders(user_id = user.user_id)


@router.post('/set_status')
async def set_status(status: str, order_id: int, user: CurrentUserDep, session: SessionDep):
    order_service = OrderService(session)
    await order_service.change_status(user, order_id, status)
    