from app.dao import BaseDao
from sqlalchemy import Integer, between, text, join, select, cast

from app.products.models import Category, Product

class ProductDao(BaseDao):
    # async def get_category_products(self, category):
    #     query = text("""
    #     WITH select_category_id AS (
    #         SELECT category_id
    #         FROM categories
    #         WHERE title = :category
    #     )

    #     SELECT *
    #     FROM products
    #     WHERE category_id = (SELECT select_category_id.category_id FROM select_category_id)
    #     """)
    #     params = {'category': category}
    #     products = await self.session.execute(query, params)
    #     return products.mappings().all()
    model = Product
    async def get_with_filters(self, **filters):
        query = select(self.model, Category)
        filter_methods = {
            'category': self._category_filter,
            'price': self._price_filter,
            'rating': self._rating_filter,
            'months_warranty': self._months_warranty_filter,
            'country_origin': self._country_origin_filter,
            'sale_percent': self._sale_percent_filter,
        }
        filters_not_none = {k: el for k, el in filters.items() if el != None and k in filter_methods}

        for filter, value in filters_not_none.items():
            query = filter_methods[filter](query, value)
        
        specification_filters: dict = filters['specification_filters']
        filter_specifications_not_none = {k: el for k, el in specification_filters.items()}
        
        for filter, val in filter_specifications_not_none.items():
            query = self._specification_filter_eq(query, filter, val)
        
        print(query)
        return (await self.session.execute(query)).mappings().all()
            
    def _category_filter(self, query, category):
        return query.join(Category, Product.category_id == Category.category_id).where(Category.title == category)
    
    def _price_filter(self, query, price: str):
        """
        Формат start-end
        """
        start, end = self._parse_price_filter(price)
        return query.where(between(Product.price, start, end))
    
    @staticmethod
    def _parse_price_filter(price):
        numbers = price.split('-')
        if len(numbers) != 2 or (not numbers[0].isdigit() or not numbers[1].isdigit()) or int(numbers[0]) > int(numbers[1]):
            raise ValueError('Неправильное поле price')
        return (int(numbers[0]), int(numbers[1]))

    def _rating_filter(self, query, rating):
        ge = 5 - rating
        return query.where(Product.rating >= ge)

    def _months_warranty_filter(self, query, months_warranty):
        return query.where(Product.months_warranty == months_warranty)

    def _country_origin_filter(self, query, origin):
        return query.where(Product.months_warranty == origin)

    def _sale_percent_filter(self, query, percent):
        return query.where(Product.percent >= percent)
    
    def _specification_filter_eq(self, query, key, value: str):
        if not value.isdigit():
            return query.where(Product.specification[key].astext == value)
        return query.where(Product.specification[key].astext == value)
    
    async def update_ratings(self, ratings: list[dict]):
        query = text('''
                    UPDATE products
                    SET rating = :rating
                    WHERE product_id = :product_id
                     ''')
        for rating in ratings:
            params = {
                'product_id': rating.product_id,
                'rating': rating.rating 
            }
            print(params)
            await self.session.execute(query, params)
    
class ReviewDao(BaseDao):
    async def rating_of_products(self):
        query = text("""SELECT product_id, ROUND(AVG(rating), 1) AS rating
                        FROM reviews
                        GROUP BY product_id""")
        result = await self.session.execute(query)
        return result.fetchall()

class CategoryDao(BaseDao):
    model = Category