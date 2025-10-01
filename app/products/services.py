from pydantic import ValidationError
from sqlalchemy import update
from app.email.email_template import new_product_email
from app.exceptions import HttpExc403Forbidden, HttpExc422UnprocessableEntity
from app.products.dao import CategoryDao, ProductDao, ProductSyncDao, ReviewDao, ReviewSyncDao
from app.products.models import Product
from app.products.schema import ProductSchema
from app.products.schema_specifications import specification_schemas_dict
from app.tasks.tasks import send_email_about_new_product
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schema import UserSchema
from fastapi import HTTPException, status

class ProductService:
    def __init__(self, session: AsyncSession, product_dao: ProductDao, category_dao: CategoryDao):
        self.product_dao = ProductDao(session)
        self.category_dao = CategoryDao(session)
        self.session = session
    
    
    @staticmethod
    def _validate_seller(user: UserSchema):
        if user.role != 'seller':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Нет прав для доступа к этому ресурсу')
        
        
    async def _get_class_name(self, product: ProductSchema):
        category_row = await self.category_dao.find_by_filter_one(category_id=product.category_id)
        return category_row.class_name
    
    
    def _validate_specification(self, product: ProductSchema, class_name):
        try:
            specification_schema = specification_schemas_dict[class_name]
            specification_schema(**product.specification)
        except ValidationError as e:
            print(e)
            raise HttpExc422UnprocessableEntity('')
        
        
    async def _add(self, product: ProductSchema):
        product = product.model_dump()
        await self.product_dao.add(**product)
        
        
    async def add_product(self, product: ProductSchema, user, flag_notification: bool):
        '''
            Добавляет товар со всеми проверками. Ес
        '''
        self._validate_seller(user)
        class_name_for_validate = await self._get_class_name(product)
        self._validate_specification(product, class_name_for_validate)
        await self._add(product)
        
        if flag_notification:
            user_emails = await self.product_dao.get_user_emails_for_send_emails_about_new_product(product)
            for email in user_emails:
                send_email_about_new_product.delay(email, title=product.title, price=product.price)
    
        
        
    async def recomendation(self, user_id):
        avg_price = await self.product_dao.avg_price(user_id)
        if avg_price:
            return await self.product_dao.get_recomentation_with_avg_price(user_id, avg_price)
        else:
            return await self.product_dao.get_recomentation(user_id)
        
        
    
    async def get_product_by_id(self, product_id):
        '''Получение продукта с id с повышением числа просмотров'''
        
        product = await self.product_dao.find_by_id(product_id)
        if not product:
            raise HttpExc422UnprocessableEntity('Продукта с таким id не существует')
        product.views += 1
        query_update = update(Product).where(Product.product_id==product_id).values(views=product.views)
        await self.session.execute(query_update)
        await self.session.commit()
        return product
    
class ProductServiceSync:
    def __init__(self, product_sync_dao: ProductSyncDao, review_sync_dao: ReviewSyncDao):
        self.product_sync_dao = product_sync_dao
        self.review_sync_dao = review_sync_dao
        
    def update_reviews(self):
        avg_reviews = self.review_sync_dao.rating_of_products()
        self.product_sync_dao.update_avg_reviews(avg_reviews)
    
        