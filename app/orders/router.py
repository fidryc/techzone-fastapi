from fastapi import APIRouter, Depends, Request, Response

from app.database import get_session
from app.orders.schema import OrderDeliveryDetailSchema, OrderPickUpDetailSchema
from app.orders.services import BasketService, OrderDeliveryService, OrderPickUpService, OrderService
from app.products.services import ProductService
from app.users.servises import UserService

router = APIRouter(
    prefix='/orders',
    tags=['Заказы']
)


@router.post('/add_to_basket')
async def add_to_basket(request: Request, response: Response, product_id: int, session=Depends(get_session)):
    '''Создание заказа с самовывозом со статусом new с товарами из basket'''
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    basket_service = BasketService(session)
    return await basket_service.add_to_basket(product_id, user.user_id)


@router.post('/create_order_pickup')
async def create_order_pickup(request: Request, response: Response, order_details: OrderPickUpDetailSchema, session=Depends(get_session)):
    '''Создание заказа с самовывозом со статусом new с товарами из basket'''
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    
    order_service = OrderPickUpService(session)
    return await order_service.create_order_pickup(user.user_id, order_details.model_dump())


@router.post('/create_order_delivery')
async def create_order_delivery(request: Request, response: Response, order_details: OrderDeliveryDetailSchema, session=Depends(get_session)):
    '''Создание заказа с доставкой со статусом new с товарами из basket'''
    
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    
    order_service = OrderDeliveryService(session)
    return await order_service.create_order_delivery(user.user_id, order_details.model_dump())


@router.get('/get_orders')
async def get_orders(request: Request, response: Response, session=Depends(get_session)):
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    order_service = OrderService(session)
    return await order_service.get_orders(user_id = user.user_id)


@router.post('/set_confirm_status')
async def set_confirm_status(request: Request, response: Response, status: str, order_id: int, session=Depends(get_session)):
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    order_service = OrderService(session)
    await order_service.change_status(user, order_id, status)
    