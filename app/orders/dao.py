from sqlalchemy import text
from app.dao import BaseDao
from app.orders.models import Order, OrderDeliveryDetail, OrderPickUpDetail, Purchase
from app.orders.schema import OrderPickUpDetailSchema
from app.orders.models import Basket
from sqlalchemy import insert, values


class BasketDao(BaseDao):
    model = Basket
    
    async def add_product(self, product_id, user_id):
        query = text('''
                     INSERT INTO baskets (product_id, user_id)
                     VALUES (:product_id, :user_id)
                     ''')
        params = {
            'product_id': product_id,
            'user_id': user_id
        }
        await self.session.execute(query, params)
        
    async def price_of_basket(self, user_id):
        query = text('''
                     SELECT SUM(price) as price
                     FROM baskets JOIN products USING (product_id)
                     WHERE user_id = :user_id
                     ''')
        params = {'user_id': user_id}
        return (await self.session.execute(query, params)).scalar()
         
         
        
    async def delete_user_basket(self, user_id):
        query = text('''
                        DELETE FROM baskets
                        WHERE user_id = :user_id
                        ''')
        params = {
            'user_id': user_id
        }
        await self.session.execute(query, params)
        
    async def basket_of_user(self, user_id) -> list[tuple[int, int]]:
        query = text('''
                     SELECT user_id, product_id
                     FROM baskets
                     WHERE user_id = :user_id
                     ''')
        params = {
            'user_id': user_id
        }
        return (await self.session.execute(query, params)).fetchall()
    
    async def delete_basket_of_user(self, user_id) -> None:
        query = text('''
                     DELETE FROM baskets
                     WHERE user_id = :user_id
                     ''')
        params = {
            'user_id': user_id
        }
        return await self.session.execute(query, params)

class OrderDao(BaseDao):
    model = Order
    
    async def change_status(self, status, order_id):
        query = text("""
                     UPDATE orders
                     SET status = :status
                     WHERE order_id = :order_id
                     """)
        params = {
            'status': status,
            'order_id': order_id
        }
        return await self.session.execute(query, params)
    
    # async def confirm_order_availability(self, user_id, order_id):
    #     """Проверяет, что пользователь владеет заказом order_id"""
    #     query = text("""
    #                  select orders
    #                  SET status = :status
    #                  WHERE orde_id = :order_id
    #                  """)
    #     params = {
    #         'status': status,
    #         'order_id': order_id
    #     }
    #     return self.session.execute(query, params)
        
    async def add_and_return_id(self, **details):
        query = insert(self.model).values(**details).returning(Order.order_id)
        print(query)
        res = await self.session.execute(query)
        print(res)
        return res.scalar()

class OrderPickUpDetailsDao(BaseDao):
    model = OrderPickUpDetail
    
    async def add_and_return_id(self, **details):
        print(details)
        query = insert(self.model).values(**details).returning(OrderPickUpDetail.order_pickup_detail_id)
        res = await self.session.execute(query)
        return res.scalar()
    
class OrderDeliveryDetailDao(BaseDao):
    model = OrderDeliveryDetail
    
    async def add_and_return_id(self, **details):
        query = insert(self.model).values(**details).returning(OrderDeliveryDetail.order_delivery_detail_id)
        res = await self.session.execute(query)
        return res.scalar()

    
class PurchaseDao(BaseDao):
    model = Purchase
    
    async def add_products_of_order(self, basket_of_user, order_id):
        data_for_insert = []
        for user_id, product_id in basket_of_user:
            data_for_insert.append({'order_id': order_id, 'product_id': product_id})
        query = insert(self.model).values(data_for_insert)
        await self.session.execute(query)
        
    
