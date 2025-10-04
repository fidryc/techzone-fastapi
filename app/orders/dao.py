from sqlalchemy import text
from app.dao import BaseDao
from app.orders.models import Order, OrderDeliveryDetail, OrderPickUpDetail, Purchase
from app.orders.models import Basket
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from app.logger import create_msg_db_error, logger
from fastapi import HTTPException, status


class BasketDao(BaseDao):
    model = Basket
    
    async def add_product(self, product_id: int, user_id: int):
        """Добавление в корзину товара"""
        logger.debug('Adding product to basket', extra={'product_id': product_id, 'user_id': user_id})
        query = text('''
                     INSERT INTO baskets (product_id, user_id)
                     VALUES (:product_id, :user_id)
                     ''')
        params = {
            'product_id': product_id,
            'user_id': user_id
        }
        try:
            await self.session.execute(query, params)
            logger.debug('Successfully added product to basket', extra={'product_id': product_id, 'user_id': user_id})
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot add_product to basket')
            logger.error(msg, extra={'product_id': product_id, 'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add product to basket"
            )
        
    async def price_of_basket(self, user_id: int) -> float:
        """Получение стоимости текущей корзины пользователя"""
        logger.debug('Calculating basket price', extra={'user_id': user_id})
        query = text('''
                     SELECT SUM(price) as price
                     FROM baskets JOIN products USING (product_id)
                     WHERE user_id = :user_id
                     ''')
        params = {'user_id': user_id}
        try:
            result = (await self.session.execute(query, params)).scalar()
            price = result if result is not None else 0
            logger.debug('Basket price calculated', extra={'user_id': user_id, 'price': price})
            return price
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot calculate price_of_basket')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate basket price"
            )
        
    async def basket_of_user(self, user_id: int) -> list[tuple[int, int]]:
        """Получение корзины пользователя"""
        logger.debug('Getting basket contents', extra={'user_id': user_id})
        query = text('''
                     SELECT user_id, product_id
                     FROM baskets
                     WHERE user_id = :user_id
                     ''')
        params = {
            'user_id': user_id
        }
        try:
            result = (await self.session.execute(query, params)).fetchall()
            logger.debug('Basket contents retrieved', extra={'user_id': user_id, 'items_count': len(result)})
            return result
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot get basket_of_user')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get basket"
            )
    
    async def delete_basket_of_user(self, user_id) -> list[int]:
        """Удаление корзины пользователя"""
        logger.debug('Deleting user basket', extra={'user_id': user_id})
        query = text('''
                     DELETE FROM baskets
                     WHERE user_id = :user_id
                     RETURNING basket_id
                     ''')
        params = {
            'user_id': user_id
        }
        try:
            deleted_ids = (await self.session.execute(query, params)).scalars().all()
            logger.debug('User basket deleted', extra={'user_id': user_id, 'deleted_count': len(deleted_ids)})
            return deleted_ids
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot delete_basket_of_user')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete basket"
            )


class OrderDao(BaseDao):
    model = Order
    
    async def change_status(self, status: str, order_id: int):
        """Смена статуса заказ"""
        logger.debug('Changing order status', extra={'order_id': order_id, 'new_status': status})
        query = text("""
                     UPDATE orders
                     SET status = :status
                     WHERE order_id = :order_id
                     """)
        params = {
            'status': status,
            'order_id': order_id
        }
        try:
            result = await self.session.execute(query, params)
            if result.rowcount == 0:
                logger.warning('Order not found for status change', extra={'order_id': order_id})
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            logger.debug('Order status changed successfully', extra={'order_id': order_id, 'new_status': status})
            return result
        except HTTPException:
            raise
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot change_status')
            logger.error(msg, extra={'status': status, 'order_id': order_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change order status"
            )
        
    async def add_and_return_id(self, **details):
        """Добавление заказа с возвратом id"""
        logger.debug('Creating new order', extra={'details': details})
        query = insert(self.model).values(**details).returning(Order.order_id)
        try:
            res = await self.session.execute(query)
            order_id = res.scalar()
            logger.debug('Order created successfully', extra={'order_id': order_id})
            return order_id
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot add_and_return_id for Order')
            logger.error(msg, extra={'details': details}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order"
            )
    
    async def delete_all_user_orders(self, user_id: int) -> list[int]:
        """Удаление всех заказов пользователя"""
        logger.debug('Deleting all user orders', extra={'user_id': user_id})
        query = text('''DELETE FROM orders
                     WHERE user_id = :user_id
                     RETURNING order_id''')
        try:
            deleted_ids = (await self.session.execute(query, params={'user_id': user_id})).scalars().all()
            logger.debug('User orders deleted', extra={'user_id': user_id, 'deleted_count': len(deleted_ids)})
            return deleted_ids
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot delete_all_user_orders')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user orders"
            )

    async def get_active_user_orders(self, user_id: int) -> list[int]:
        """Получение актуальных заказов пользователя"""
        logger.debug('Getting active user orders', extra={'user_id': user_id})
        query = text('''
                     SELECT order_id
                     FROM orders
                     WHERE user_id = :user_id AND 
                     (status != 'finished' AND status != 'cancelled')
                     ''')
        try:
            active_orders = (await self.session.execute(query, params={'user_id': user_id})).scalars().all()
            logger.debug('Active orders retrieved', extra={'user_id': user_id, 'orders_count': len(active_orders)})
            return active_orders
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot get_active_user_orders')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get active orders"
            )


class OrderPickUpDetailsDao(BaseDao):
    model = OrderPickUpDetail
    
    async def add_and_return_id(self, **details):
        """Создание заказа с самовывозом и возврат id"""
        logger.debug('Creating order pickup details', extra={'details': details})
        query = insert(self.model).values(**details).returning(OrderPickUpDetail.order_pickup_detail_id)
        try:
            res = await self.session.execute(query)
            detail_id = res.scalar()
            logger.debug('Pickup details created successfully', extra={'order_pickup_detail_id': detail_id})
            return detail_id
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot add_and_return_id for OrderPickUpDetail')
            logger.error(msg, extra={'details': details}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create pickup details"
            )
    

class OrderDeliveryDetailDao(BaseDao):
    model = OrderDeliveryDetail
    
    async def add_and_return_id(self, **details):
        """Создание заказа с доставкой и возврат id"""
        logger.debug('Creating order delivery details', extra={'details': details})
        query = insert(self.model).values(**details).returning(OrderDeliveryDetail.order_delivery_detail_id)
        try:
            res = await self.session.execute(query)
            detail_id = res.scalar()
            logger.debug('Delivery details created successfully', extra={'order_delivery_detail_id': detail_id})
            return detail_id
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot add_and_return_id for OrderDeliveryDetail')
            logger.error(msg, extra={'details': details}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create delivery details"
            )

    
class PurchaseDao(BaseDao):
    model = Purchase
    
    async def add_products_of_order(self, basket_of_user, order_id):
        """Добавление товаров заказа в purchase"""
        logger.debug('Adding products to order', extra={'order_id': order_id, 'basket_items': len(basket_of_user)})
        data_for_insert = []
        for user_id, product_id in basket_of_user:
            data_for_insert.append({'order_id': order_id, 'product_id': product_id})
        query = insert(self.model).values(data_for_insert)
        try:
            await self.session.execute(query)
            logger.debug('Products added to order successfully', extra={'order_id': order_id, 'products_count': len(data_for_insert)})
        except SQLAlchemyError:
            msg = create_msg_db_error('Cannot add_products_of_order')
            logger.error(msg, extra={'order_id': order_id, 'products_count': len(data_for_insert)}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add products to order"
            )
