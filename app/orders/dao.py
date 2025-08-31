from sqlalchemy import text
from app.dao import BaseDao
from app.products.models import Basket


class BasketDao(BaseDao):
    model = Basket
    
    async def add_product(self, product_id, user_id):
        query = text('''
                     UPDATE baskets
                     SET product_id = :product_id
                     WHERE user_id = :user_id
                     ''')
        params = {
            'product_id': product_id,
            'user_id': user_id
        }
        await self.session.execute(query, params)
        
