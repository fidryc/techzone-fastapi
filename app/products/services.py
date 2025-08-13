from pydantic import ValidationError
from app.exceptions import HttpExc403Conflict, HttpExc422
from app.products.dao import CategoryDao, ProductDao, ReviewDao
from app.products.schema import ProductSchema
from app.products.schema_specifications import specification_schemas_dict

class ProductService:
    def __init__(self, session):
        self.product_dao = ProductDao(session)
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
        
    async def add_product(self, product: ProductSchema, user):
        '''
            Добавляет товар со всеми проверками
        '''
        self._validate_seller(user)
        class_name_for_validate = await self._get_class_name(product)
        self._validate_specification(product, class_name_for_validate)
        await self._add(product)
        
    async def update_ratings(self):
        ratings = await self.review_dao.rating_of_products()
        await self.product_dao.update_ratings(ratings)
        await self.session.commit()
        