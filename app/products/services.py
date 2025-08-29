from pydantic import ValidationError
from app.email.email_template import new_product_email
from app.exceptions import HttpExc403Conflict, HttpExc422
from app.products.dao import CategoryDao, ProductDao, ProductSyncDao, ReviewDao
from app.products.schema import ProductSchema
from app.products.schema_specifications import specification_schemas_dict
from app.tasks.tasks import send_email_about_new_product

class ProductService:
    def __init__(self, session):
        self.product_dao = ProductDao(session)
        self.product_sync_dao = ProductSyncDao(session)
        self.category_dao = CategoryDao(session)
        self.review_dao = ReviewDao(session)
        self.session = session
    
    @staticmethod
    def _validate_seller(user):
        if user.role != 'seller':
            raise HttpExc403Conflict('Нет доступа')
        
    async def _get_class_name(self, product: ProductSchema):
        category_row = await self.category_dao.find_by_filter_one(category_id=product.category_id)
        return category_row.class_name
    
    def _validate_specification(self, product: ProductSchema, class_name):
        try:
            specification_schema = specification_schemas_dict[class_name]
            specification_schema(**product.specification)
        except ValidationError as e:
            print(e)
            raise HttpExc422('')
        
    async def _add(self, product: ProductSchema):
        product = product.model_dump()
        await self.product_dao.add(**product)
        
    async def add_product(self, product: ProductSchema, user, flag_notification: bool):
        '''
            Добавляет товар со всеми проверками
        '''
        self._validate_seller(user)
        class_name_for_validate = await self._get_class_name(product)
        self._validate_specification(product, class_name_for_validate)
        await self._add(product)
        
        if flag_notification:
            user_emails = await self.product_dao.get_user_emails_for_send_emails_about_new_product(product)
            for email in user_emails:
                send_email_about_new_product.delay(email, title=product.title, price=product.price)
                
            
        
    async def update_ratings(self):
        ratings = await self.review_dao.rating_of_products()
        await self.product_dao.update_ratings(ratings)
        await self.session.commit()
        
    async def recomendation(self, user_id):
        avg_price = await self.product_dao.avg_price(user_id)
        if avg_price:
            return await self.product_dao.get_recomentation_with_avg_price(user_id, avg_price)
        else:
            return await self.product_dao.get_recomentation(user_id)
        
    def update_reviews(self):
        
        avg_reviews = self.product_sync_dao.get_avg_reviews()
        self.product_sync_dao.update_avg_reviews(avg_reviews)
        
    
        