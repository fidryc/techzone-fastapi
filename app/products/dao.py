from abc import abstractmethod
from app.dao import BaseDao, BaseSyncDao
from sqlalchemy import Integer, between, text, join, select, cast, update

from app.products.models import Category, HistoryQueryUser, Product

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
    
    async def find_by_id(self, product_id):
        query = select(Product).where(Product.product_id==product_id)
        product = (await self.session.execute(query)).scalar_one_or_none()
        return product
    
    
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
        
    async def avg_price(self, user_id):
        """Получение средней цены товара купленного пользователем"""
        params = {'user_id': user_id}
        query = text("""SELECT AVG(products.price) AS avg_price FROM public.purchases
                    JOIN orders USING(order_id)
                    JOIN products USING (product_id)
                    WHERE user_id = :user_id""")
        return (await self.session.execute(query, params=params)).scalars().one_or_none()
    
    async def get_recomentation_with_avg_price(self, user_id, avg_price):
        """Рекомендации с фильтрацией по средней цене"""
        params = {'user_id': user_id, 'avg_price': avg_price}
        query = text("""WITH favorite_cats AS (
                            SELECT category_id FROM public.favorite_products
                            JOIN products USING (product_id)
                            WHERE user_id = :user_id
                            GROUP BY (user_id, category_id)
                            ORDER BY COUNT(category_id) DESC
                            LIMIT 5),
                        popular_not_in_fav_cats AS (
                            SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                            FROM products
                            WHERE category_id not in (SELECT category_id FROM favorite_cats)
                            ORDER BY rating DESC, views DESC
                            LIMIT 30
                        ),
                        popular_in_fav_cats AS (
                            SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                            FROM products
                            WHERE category_id in (SELECT category_id FROM favorite_cats)
                            ORDER BY rating DESC, views DESC
                            LIMIT 60
                        ),
                        union_tables AS (
                            SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                            FROM popular_not_in_fav_cats
                            UNION 
                            SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                            FROM popular_in_fav_cats
                        )
                        SELECT *
                        FROM union_tables
                        ORDER BY ABS(price - :avg_price) ASC""")
        return (await self.session.execute(query, params=params)).mappings().all()
    
    async def get_recomentation(self, user_id):
        params = {'user_id': user_id}
        query = text("""WITH favorite_cats AS (
                        SELECT category_id FROM public.favorite_products
                        JOIN products USING (product_id)
                        WHERE user_id = :user_id
                        GROUP BY (user_id, category_id)
                        ORDER BY COUNT(category_id) DESC
                        LIMIT 5),
                        popular_not_in_fav_cats AS (
                        SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                        FROM products
                        WHERE category_id not in (SELECT category_id FROM favorite_cats)
                        ORDER BY rating DESC, views DESC
                        LIMIT 30
                        ),
                        popular_in_fav_cats AS (
                        SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                        FROM products
                        WHERE category_id in (SELECT category_id FROM favorite_cats)
                        ORDER BY rating DESC, views DESC
                        LIMIT 60
                        )
                        SELECT * FROM popular_not_in_fav_cats
                        UNION SELECT * FROM popular_in_fav_cats
                        ORDER BY rating DESC """)
        return (await self.session.execute(query, params=params)).mappings().all()

    async def get_user_emails_for_send_emails_about_new_product(self, product):
        """Получение пользователей, которым нужно отправить email о появлении товара в их любимой категории"""
        params = {
            'category_id': product.category_id
        }
        query = text("""WITH count_favs AS (
                    SELECT user_id, category_id, COUNT(category_id) AS count_products
                    FROM favorite_products JOIN products USING (product_id)
                    GROUP BY (user_id, category_id)
                ),
                rank_categories AS (
                    SELECT user_id, category_id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY count_products DESC) AS rn
                    FROM count_favs
                ),
                fav_categories AS (
                    SELECT user_id, category_id FROM rank_categories
                    WHERE rn = 1
                )
                SELECT email
                FROM fav_categories
                JOIN users USING (user_id)
                WHERE category_id = :category_id""")
        return (await self.session.execute(query, params)).scalars().all()

# Синхронный вариант для celery
class ProductSyncDao(BaseSyncDao):
    model = Product
    
    def update_avg_reviews(self, products_avg_reviews: list[tuple[int, float]]):
        query = text("""UPDATE products
                     SET rating = :avg_review
                     WHERE product_id = :product_id""")
        for product_id, avg_review in products_avg_reviews:
            params = {
                'avg_review': float(avg_review),
                'product_id': int(product_id)
            }
            self.session.execute(query, params)

class ReviewDao(BaseDao):
    async def rating_of_products(self):
        query = text("""SELECT product_id, ROUND(AVG(rating), 1) AS rating
                        FROM reviews
                        GROUP BY product_id""")
        result = await self.session.execute(query)
        return result.fetchall()
    
class ReviewSyncDao(BaseDao):
    def rating_of_products(self):
        query = text("""SELECT product_id, ROUND(AVG(rating), 1) AS rating
                        FROM reviews
                        GROUP BY product_id""")
        return self.session.execute(query).fetchall()

class CategoryDao(BaseDao):
    model = Category
    

class HistoryQueryTextDao(BaseDao):
    model = HistoryQueryUser
    
