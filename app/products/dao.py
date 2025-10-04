from app.dao import BaseDao, BaseSyncDao
from sqlalchemy import between, text, select
from sqlalchemy.exc import SQLAlchemyError
from app.products.models import Category, HistoryQueryUser, Product
from app.products.schema import ProductSchema
from fastapi import HTTPException, status
from app.logger import logger, create_msg_db_error


class ProductDao(BaseDao):
    model = Product
    
    async def get_with_filters(self, **filters):
        """Получение товара по фильтрам"""
        try:
            query = select(self.model, Category)
            filter_methods = {
                'category': self._category_filter,
                'price': self._price_filter,
                'rating': self._rating_filter,
                'months_warranty': self._months_warranty_filter,
                'country_origin': self._country_origin_filter,
                'sale_percent': self._sale_percent_filter,
            }
            filters_not_none = {k: el for k, el in filters.items() if el is not None and k in filter_methods}

            for filter_name, value in filters_not_none.items():
                query = filter_methods[filter_name](query, value)
            
            specification_filters: dict = filters.get('specification_filters', {})
            
            for key, val in specification_filters.items():
                query = self._specification_filter_eq(query, key, val)
            
            results = (await self.session.execute(query)).mappings().all()
            logger.debug('Products filtered successfully', extra={
                'filters_count': len(filters_not_none),
                'spec_filters_count': len(specification_filters),
                'results_count': len(results)
            })
            return results
            
        except ValueError as e:
            logger.warning('Invalid filter value', extra={'filters': filters}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get products with filters')
            logger.error(msg, extra={'filters': filters}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении товаров с фильтрами'
            )
        except Exception as e:
            logger.error('Unexpected error filtering products', extra={'filters': filters}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при фильтрации товаров'
            )
    
    async def find_by_id(self, product_id):
        """Нахождение товара по product_id"""
        try:
            query = select(Product).where(Product.product_id == product_id)
            product = (await self.session.execute(query)).scalar_one_or_none()
            logger.debug('Product search by id', extra={'product_id': product_id, 'found': product is not None})
            return product
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to find product by id')
            logger.error(msg, extra={'product_id': product_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при поиске товара по id'
            )
        except Exception as e:
            logger.error('Unexpected error finding product by id', extra={'product_id': product_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при поиске товара'
            )
    
    def _category_filter(self, query, category):
        """Добавляет к текущему запросу фильтр по категории"""
        logger.debug('Applying category filter', extra={'category': category})
        return query.join(Category, Product.category_id == Category.category_id).where(Category.title == category)
    
    def _price_filter(self, query, price: str):
        """Добавляет к текущему запросу фильтр по цене формата start-end"""
        start, end = self._parse_price_filter(price)
        logger.debug('Applying price filter', extra={'start': start, 'end': end})
        return query.where(between(Product.price, start, end))
    
    @staticmethod
    def _parse_price_filter(price):
        """Парсинг фильтра по цене и валидирует его"""
        numbers = price.split('-')
        if len(numbers) != 2 or (not numbers[0].isdigit() or not numbers[1].isdigit()) or int(numbers[0]) > int(numbers[1]):
            raise ValueError('Неправильное поле price. Формат: start-end, где start <= end')
        return (int(numbers[0]), int(numbers[1]))

    def _rating_filter(self, query, rating):
        """Добавляет к текущему запросу фильтр по рейтингу (1: от 4 и выше, 2: от 3 и выше и т.д.)"""
        ge = 5 - rating
        logger.debug('Applying rating filter', extra={'rating_min': ge})
        return query.where(Product.rating >= ge)

    def _months_warranty_filter(self, query, months_warranty):
        """Добавляет к текущему запросу фильтр по месяцам гарантии"""
        logger.debug('Applying warranty filter', extra={'months': months_warranty})
        return query.where(Product.months_warranty == months_warranty)

    def _country_origin_filter(self, query, origin):
        """Добавляет к текущему запросу фильтр по стране производства"""
        logger.debug('Applying country filter', extra={'country': origin})
        return query.where(Product.country_origin == origin)

    def _sale_percent_filter(self, query, percent):
        """Добавляет к текущему запросу фильтр по проценту скидки"""
        logger.debug('Applying sale filter', extra={'percent': percent})
        return query.where(Product.sale_percent >= percent)
    
    def _specification_filter_eq(self, query, key: str, value: str):
        """Фильтр для характеристик товара по равенству значения по ключу с полем"""
        logger.debug('Applying specification filter', extra={'key': key, 'value': value})
        return query.where(Product.specification[key].astext == value)
        
    async def avg_price(self, user_id: int) -> float:
        """Получение средней цены товара купленного пользователем"""
        try:
            params = {'user_id': user_id}
            query = text("""SELECT AVG(products.price) AS avg_price FROM public.purchases
                        JOIN orders USING(order_id)
                        JOIN products USING (product_id)
                        WHERE user_id = :user_id""")
            result = (await self.session.execute(query, params=params)).scalars().one_or_none()
            logger.debug('Average price calculated', extra={'user_id': user_id, 'avg_price': result})
            return result
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to calculate average price')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при расчете средней цены'
            )
        except Exception as e:
            logger.error('Unexpected error calculating average price', extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при расчете средней цены'
            )
    
    async def get_recomentation_with_avg_price(self, user_id: int, avg_price: float) -> list[Product]:
        """Рекомендации с фильтрацией по средней цене"""
        try:
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
            results = (await self.session.execute(query, params=params)).mappings().all()
            logger.info('Recommendations with avg price retrieved', extra={'user_id': user_id, 'avg_price': avg_price, 'count': len(results)})
            return results
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get recommendations with avg price')
            logger.error(msg, extra={'user_id': user_id, 'avg_price': avg_price}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении рекомендаций'
            )
        except Exception as e:
            logger.error('Unexpected error getting recommendations with avg price', extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении рекомендаций'
            )
    
    async def get_recomentation(self, user_id: int) -> list[Product]:
        """Получение рекомендаций для пользователя с любимыми товарами без средней цены товара"""
        try:
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
            results = (await self.session.execute(query, params=params)).mappings().all()
            logger.info('Recommendations retrieved', extra={'user_id': user_id, 'count': len(results)})
            return results
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get recommendations')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении рекомендаций'
            )
        except Exception as e:
            logger.error('Unexpected error getting recommendations', extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении рекомендаций'
            )
    
    async def get_recomentation_for_new_user(self) -> list[Product]:
        """Рекомендации для пользователей без статистики"""
        try:
            query = text("""
                            SELECT product_id, title, category_id, specification, price, rating, description, months_warranty, country_origin, sale_percent, views
                            FROM products
                            ORDER BY rating DESC, views DESC
                            LIMIT 30
                            """)
            results = (await self.session.execute(query)).mappings().all()
            logger.info('Recommendations for new user retrieved', extra={'count': len(results)})
            return results
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get recommendations for new user')
            logger.error(msg, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении рекомендаций'
            )
        except Exception as e:
            logger.error('Unexpected error getting recommendations for new user', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении рекомендаций'
            )

    async def get_user_emails_for_send_emails_about_new_product(self, product: ProductSchema) -> list[str]:
        """Получение пользователей, которым нужно отправить email о появлении товара в их любимой категории"""
        try:
            params = {'category_id': product.category_id}
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
            results = (await self.session.execute(query, params)).scalars().all()
            logger.info('Interested users retrieved for new product notification', extra={
                'category_id': product.category_id,
                'recipients_count': len(results)
            })
            return results
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get user emails for notifications')
            logger.error(msg, extra={'category_id': product.category_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении пользователей для уведомлений'
            )
        except Exception as e:
            logger.error('Unexpected error getting user emails for notifications', extra={'category_id': product.category_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении пользователей для уведомлений'
            )
    
    async def favorite_products(self, user_id: int) -> list[int]:
        """Получение ID любимых продуктов пользователя"""
        try:
            query = text("""
                         SELECT product_id
                         FROM favorite_products
                         WHERE user_id = :user_id
                         """)
            results = (await self.session.execute(query, params={'user_id': user_id})).scalars().all()
            logger.debug('Favorite products retrieved', extra={'user_id': user_id, 'count': len(results)})
            return results
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get favorite products')
            logger.error(msg, extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении любимых продуктов'
            )
        except Exception as e:
            logger.error('Unexpected error getting favorite products', extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении любимых продуктов'
            )


# Синхронный вариант для celery
class ProductSyncDao(BaseSyncDao):
    model = Product
    
    def update_avg_reviews(self, products_avg_reviews: list[tuple[int, float]]):
        """Обновление средних оценок товаров"""
        try:
            query = text("""UPDATE products
                         SET rating = :avg_review
                         WHERE product_id = :product_id""")
            for product_id, avg_review in products_avg_reviews:
                params = {
                    'avg_review': float(avg_review),
                    'product_id': int(product_id)
                }
                self.session.execute(query, params)
            logger.info('Average reviews updated (sync)', extra={'count': len(products_avg_reviews)})
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to update average reviews (sync)')
            logger.error(msg, extra={'count': len(products_avg_reviews)}, exc_info=True)
            raise
        except Exception as e:
            logger.error('Unexpected error updating average reviews (sync)', extra={'count': len(products_avg_reviews)}, exc_info=True)
            raise


class ReviewDao(BaseDao):
    async def rating_of_products(self):
        """Получение product_id с их средней оценкой"""
        try:
            query = text("""SELECT product_id, ROUND(AVG(rating), 1) AS rating
                            FROM reviews
                            GROUP BY product_id""")
            result = await self.session.execute(query)
            ratings = result.fetchall()
            logger.debug('Product ratings calculated', extra={'count': len(ratings)})
            return ratings
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get product ratings')
            logger.error(msg, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении рейтингов продуктов'
            )
        except Exception as e:
            logger.error('Unexpected error getting product ratings', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении рейтингов'
            )
    

class ReviewSyncDao(BaseDao):
    def rating_of_products(self):
        """Получение product_id с их средней оценкой (sync)"""
        try:
            query = text("""SELECT product_id, ROUND(AVG(rating), 1) AS rating
                            FROM reviews
                            GROUP BY product_id""")
            ratings = self.session.execute(query).fetchall()
            logger.debug('Product ratings calculated (sync)', extra={'count': len(ratings)})
            return ratings
        except SQLAlchemyError as e:
            msg = create_msg_db_error('Failed to get product ratings (sync)')
            logger.error(msg, exc_info=True)
            raise
        except Exception as e:
            logger.error('Unexpected error getting product ratings (sync)', exc_info=True)
            raise


class CategoryDao(BaseDao):
    model = Category
    

class HistoryQueryTextDao(BaseDao):
    model = HistoryQueryUser