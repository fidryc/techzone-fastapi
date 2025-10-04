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


@router.post('/add_to_basket', summary='Добавление товара в корзину')
async def add_to_basket(user: CurrentUserDep, session: SessionDep, product_id: int):
    """
    Добавление товара в корзину пользователя
    
    Добавляет указанный товар в корзину текущего пользователя
    
    Args:
        product_id: идентификатор товара
    
    Returns:
        200: Товар успешно добавлен в корзину
    """
    basket_service = BasketService(session)
    return await basket_service.add_to_basket(product_id, user.user_id)


@router.post('/create_order_pickup', summary='Создание заказа с самовывозом')
async def create_order_pickup(user: CurrentUserDep, session: SessionDep, order_details: OrderPickUpDetailSchema):
    """
    Создание заказа с самовывозом
    
    Создает новый заказ со статусом 'new' с товарами из корзины и данными для самовывоза
    
    Args:
        order_details: данные заказа для самовывоза
    
    Returns:
        200: Заказ с самовывозом успешно создан
    """
    order_service = OrderPickUpService(session)
    return await order_service.create_order_pickup(user.user_id, order_details.model_dump())


@router.post('/create_order_delivery', summary='Создание заказа с доставкой')
async def create_order_delivery(user: CurrentUserDep, session: SessionDep, order_details: OrderDeliveryDetailSchema):
    """
    Создание заказа с доставкой
    
    Создает новый заказ со статусом 'new' с товарами из корзины и данными для доставки
    
    Args:
        order_details: данные заказа для доставки
    
    Returns:
        200: Заказ с доставкой успешно создан
    """
    order_service = OrderDeliveryService(session)
    return await order_service.create_order_delivery(user.user_id, order_details.model_dump())


@router.get('/get_orders', summary='Получение списка заказов')
async def get_orders(user: CurrentUserDep, session: SessionDep):
    """
    Получение списка заказов пользователя
    
    Возвращает все заказы текущего пользователя
    
    Returns:
        Список заказов пользователя
    """
    order_service = OrderService(session)
    return await order_service.get_orders(user_id = user.user_id)


@router.post('/set_status', summary='Изменение статуса заказа')
async def set_status(status: str, order_id: int, user: CurrentUserDep, session: SessionDep):
    """
    Изменение статуса заказа
    
    Обновляет статус указанного заказа
    
    Args:
        status: новый статус заказа
        order_id: идентификатор заказа
    
    Returns:
        200: Статус заказа успешно изменен
    """
    order_service = OrderService(session)
    await order_service.change_status(user, order_id, status)