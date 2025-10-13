from sqlalchemy import text
from app.dao import BaseDao
from app.stores.models import StoreQuantityInfo
from app.stores.schema import StoreQuantityInfoSchema
class StoreQuantityInfoDao(BaseDao):
    model = StoreQuantityInfo
     
    async def get_quantity_of_product(self, store_id: int, product_id: int) -> int:
        quantity_in_store: list[StoreQuantityInfoSchema] = await self.find_by_filter(store_id=store_id, product_id = product_id)
        if not quantity_in_store:
            return 0
        else:
            return quantity_in_store[0].quantity
        
    async def get_missing_products(self, products_with_quantity: list[int, int], store_id):
        """Получение товаров, которых не хватает в магазине"""
        missing_products = []
        for product_id, quantity_basket in products_with_quantity:
            quantity_in_store = await self.get_quantity_of_product(store_id=store_id, product_id = product_id)
            if not quantity_in_store or quantity_basket > quantity_in_store:
                missing_products.append(product_id)
        return missing_products
    
    async def reduction_in_quantity(self, products_with_quantity: list[int, int], store_id):
        """Уменьшение количества товаров"""
        query = text("""
                     UPDATE stores_quantity_info
                     SET quantity = quantity - :quantity
                     WHERE store_id = :store_id AND product_id = :product_id
                     """)
        for product_id, quantity in products_with_quantity:
            await self.session.execute(query, params={'store_id': store_id, 'product_id': product_id, 'quantity': quantity})