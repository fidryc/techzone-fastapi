from datetime import datetime

from sqlalchemy import text
from app.exceptions import HttpExc403Forbidden, HttpExc422UnprocessableEntity
from app.orders.dao import BasketDao, OrderDao, OrderDeliveryDetailDao, OrderPickUpDetail, OrderPickUpDetailsDao, PurchaseDao
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.products.dao import ProductDao

class BasketService:
    def __init__(self, session):
        self.basket_dao = BasketDao(session)
        self.product_dao = ProductDao(session)
        self.session: AsyncSession = session
        
    async def add_to_basket(self, product_id, user_id):
        if not await self.product_dao.find_by_filter_one(product_id = product_id):
            raise HttpExc422UnprocessableEntity('Такого товара не существует')
        await self.basket_dao.add_product(product_id, user_id)
        await self.session.commit()
class OrderService:
    def __init__(self, session):
        self.order_dao = OrderDao(session)
        
    async def get_orders(self, user_id):
        orders = await self.order_dao.find_by_filter(user_id = user_id)
        return orders[::-1]
    async def change_status(self, user, order_id, status):
        if user.role not in ('seller', 'admin'):
            raise HttpExc403Forbidden('Нет досупа к изменению этого заказа')
        await self.order_dao.change_status(status, order_id)
        await self.order_dao.session.commit()
    
class OrderPickUpService:
    def __init__(self, session):
        self.basket_dao = BasketDao(session)
        self.order_dao = OrderDao(session)
        self.order_pickup_details_dao = OrderPickUpDetailsDao(session)
        self.purchase_dao = PurchaseDao(session)
        self.session: AsyncSession = session
        
    async def create_order_pickup(self, user_id: int, order_details: dict):
        try:
            # Получаем product_id, которые лежат в корзине пользователя
            basket_of_user: list = await self.basket_dao.basket_of_user(user_id) 
            if not basket_of_user:
                raise HTTPException(400, 'Пустая корзина')
            
            # возможно стоит объединить в один запрос
            price: int = await self.basket_dao.price_of_basket(user_id) 
            # создаем запись в order_details и получаем id тк, в orders есть поле order_details_id
            order_pickup_detail_id: int = await self.order_pickup_details_dao.add_and_return_id(**order_details)
            print(order_pickup_detail_id)
            # Временный вариант, возможно стоит переписать на запрос, нельзя менять id в базе
            order = {
                'status': 'new',
                'order_type_id': 2,
                'order_detail_id': order_pickup_detail_id,
                'user_id': user_id,
                'price': price,
                'date': datetime.now(),  # или datetime.now()
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            order_id = await self.order_dao.add_and_return_id(**order)
            # Переносим все данные о покупке
            await self.purchase_dao.add_products_of_order(basket_of_user=basket_of_user, order_id=order_id)
            await self.basket_dao.delete_basket_of_user(user_id)

            await self.session.commit()
            return order_id
        except Exception as e:
            await self.session.rollback()
            
class OrderDeliveryService:
    def __init__(self, session):
        self.basket_dao = BasketDao(session)
        self.order_dao = OrderDao(session)
        self.order_delivery_detail_dao = OrderDeliveryDetailDao(session)
        self.purchase_dao = PurchaseDao(session)
        self.session: AsyncSession = session
        
    async def create_order_delivery(self, user_id: int, order_details: dict):
        try:
            # Получаем product_id, которые лежат в корзине пользователя
            basket_of_user: list = await self.basket_dao.basket_of_user(user_id) 
            print(basket_of_user)
            if not basket_of_user:
                raise HTTPException(400, 'Пустая корзина')
            
            # возможно стоит объединить в один запрос
            price: int = await self.basket_dao.price_of_basket(user_id) 
            print(price)
            # создаем запись в order_details и получаем id тк, в orders есть поле order_details_id
            order_delivery_detail_id: int = await self.order_delivery_detail_dao.add_and_return_id(**order_details)
            print(order_delivery_detail_id)
            # Временный вариант, возможно стоит переписать на запрос, нельзя менять id в базе
            order = {
                'status': 'new',
                'order_type_id': 1,
                'order_detail_id': order_delivery_detail_id,
                'user_id': user_id,
                'price': price,
                'date': datetime.now(),  # или datetime.now()
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            order_id = await self.order_dao.add_and_return_id(**order)
            # Переносим все данные о покупке
            await self.purchase_dao.add_products_of_order(basket_of_user=basket_of_user, order_id=order_id)
            await self.basket_dao.delete_basket_of_user(user_id)

            await self.session.commit()
            return order_id
        except Exception as e:
            await self.session.rollback()
            print(e)
            raise HTTPException(400)
        

        