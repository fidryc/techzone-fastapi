from pydantic import ValidationError
from sqlalchemy import update
from app.products.dao import CategoryDao, ProductDao, ProductSyncDao, ReviewSyncDao
from app.products.models import Category, Product
from app.products.schema import ProductSchema
from app.products.schema_specifications import specification_schemas_dict
from app.tasks.email_tasks import send_email_about_new_product
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.schema import UserSchema
from fastapi import HTTPException, status
from app.logger import logger


class ProductServiceSync:
    def __init__(self, product_sync_dao: ProductSyncDao, review_sync_dao: ReviewSyncDao):
        self.product_sync_dao = product_sync_dao
        self.review_sync_dao = review_sync_dao
        
    def update_reviews(self):
        """
        Обновление средних оценок у товаров
        
        Высчитываются средние оценки товаров из отзывов на товары и сохраняются в поле оценок у товаров.
        Функция написана синхронно, так как она должна запускаться фоном в celery
        """
        try:
            logger.info('Starting reviews update (sync)')
            avg_reviews = self.review_sync_dao.rating_of_products()
            self.product_sync_dao.update_avg_reviews(avg_reviews)
            logger.info('Reviews updated successfully (sync)', extra={'count': len(avg_reviews)})
        except Exception as e:
            logger.error('Failed to update reviews (sync)', exc_info=True)
            raise
    
    
class ProductService:
    def __init__(self, session: AsyncSession, product_dao: ProductDao, category_dao: CategoryDao):
        self.product_dao = product_dao
        self.category_dao = category_dao
        self.session = session
    
    @staticmethod
    def _validate_seller(user: UserSchema):
        """Проверяет является ли пользователь продавцом"""
        if user.role != 'seller':
            logger.warning('Access denied: user is not a seller', extra={'user_id': user.user_id, 'role': user.role})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Нет прав для доступа к этому ресурсу'
            )
           
    async def _get_class_name(self, product: ProductSchema):
        """Получает название класса для валидации категории"""
        try:
            category_row: Category = await self.category_dao.find_by_filter_one(category_id=product.category_id)
            if not category_row:
                logger.warning('Category not found', extra={'category_id': product.category_id})
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Категория не найдена'
                )
            logger.debug('Category class name retrieved', extra={'category_id': product.category_id, 'class_name': category_row.class_name})
            return category_row.class_name
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to get category class name', extra={'category_id': product.category_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении информации о категории'
            )
    
    def _validate_specification(self, product: ProductSchema, class_name):
        """Валидирует характеристики json поля продукта"""
        try:
            specification_schema = specification_schemas_dict.get(class_name)
            if not specification_schema:
                logger.warning('Specification schema not found', extra={'class_name': class_name})
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f'Схема спецификации для {class_name} не найдена'
                )
            
            specification_schema(**product.specification)
            logger.debug('Specification validated successfully', extra={'class_name': class_name})
            
        except ValidationError as e:
            logger.warning('Specification validation failed', extra={
                'class_name': class_name,
                'errors': str(e.errors())
            })
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'Некорректные характеристики товара: {e.errors()}'
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Unexpected error during specification validation', extra={'class_name': class_name}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при валидации характеристик'
            )
         
    async def _add(self, product: ProductSchema):
        """Переводит в dict для возможности добавить товар"""
        try:
            product_dict = product.model_dump()
            await self.product_dao.add(**product_dict)
            logger.info('Product added to database', extra={'title': product.title, 'price': product.price})
        except Exception as e:
            logger.error('Failed to add product to database', extra={'title': product.title}, exc_info=True)
            raise
         
    async def add_product(self, product: ProductSchema, user: UserSchema, flag_notification: bool):
        """
        Добавляет товар со всеми проверками
        
        Добавляет товар с проверкой является ли пользователь продавцом,
        проверкой характеристик товара, тк они находятся в json поле.
        Если нужно то отправляет всем заинтересованным пользователям email
        о появлении нового товара
        
        Args:
            product: товар (ProductSchema)
            user: пользователь, который добавляет товар (UserSchema)
            flag_notification: флаг, при True отправляются email (bool)
        """
        try:
            logger.info('Adding new product', extra={
                'title': product.title,
                'user_id': user.user_id,
                'notifications_enabled': flag_notification
            })
            
            self._validate_seller(user)
            class_name_for_validate = await self._get_class_name(product)
            self._validate_specification(product, class_name_for_validate)
            await self._add(product)
            
            if flag_notification:
                logger.info('Scheduling email notifications', extra={'title': product.title})
                user_emails = await self.product_dao.get_user_emails_for_send_emails_about_new_product(product)
                for email in user_emails:
                    send_email_about_new_product.delay(email, title=product.title, price=product.price)
                logger.info('Email notifications scheduled', extra={'recipients_count': len(user_emails)})
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to add product', extra={'title': product.title, 'user_id': user.user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при добавлении продукта'
            )
     
    async def recomendation(self, user_id):
        """
        Получение рекомендаций
        
        Получение рекомендаций с фильтрацией по средней цене купленных товаров пользователем,
        если есть покупки. Если не было, то без фильтрации по средней цене.
        Если пользователь без статистики, то выводятся просто популярные товары
        """
        try:
            logger.debug('Getting recommendations', extra={'user_id': user_id})
            
            favorite_products = await self.product_dao.favorite_products(user_id)
            if not favorite_products:
                logger.info('User has no favorites, using popular products', extra={'user_id': user_id})
                return await self.product_dao.get_recomentation_for_new_user()
            
            avg_price = await self.product_dao.avg_price(user_id)
            if avg_price:
                logger.info('Using recommendations with avg price', extra={'user_id': user_id, 'avg_price': avg_price})
                return await self.product_dao.get_recomentation_with_avg_price(user_id, avg_price)
            else:
                logger.info('Using general recommendations', extra={'user_id': user_id})
                return await self.product_dao.get_recomentation(user_id)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to get recommendations', extra={'user_id': user_id}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении рекомендаций'
            )
        
    async def get_product_by_id(self, product_id):
        """Получение продукта по id с повышением числа просмотров"""
        try:
            logger.debug('Getting product by id', extra={'product_id': product_id})
            
            product = await self.product_dao.find_by_id(product_id)
            if not product:
                logger.warning('Product not found', extra={'product_id': product_id})
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Продукта с таким id не существует'
                )
            
            product.views += 1
            query_update = update(Product).where(Product.product_id == product_id).values(views=product.views)
            await self.session.execute(query_update)
            await self.session.commit()
            
            logger.info('Product retrieved and views incremented', extra={'product_id': product_id, 'views': product.views})
            return product
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to get product by id', extra={'product_id': product_id}, exc_info=True)
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении продукта'
            )