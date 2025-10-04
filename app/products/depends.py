from typing import Annotated
from fastapi import Depends
from app.database import SessionDep
from app.products.dao import CategoryDao, ProductDao
from app.products.services import ProductService

def get_product_dao(session: SessionDep) -> ProductDao:
    return ProductDao(session)

ProductDaoDep = Annotated[ProductDao, Depends(get_product_dao)]


def get_category_dao(session: SessionDep) -> CategoryDao:
    return CategoryDao(session)

CategoryDaoDep = Annotated[CategoryDao, Depends(get_category_dao)]

def get_product_service(session: SessionDep, product_dao: ProductDaoDep, category_dao: CategoryDaoDep) -> ProductService:
    return ProductService(session, product_dao, category_dao)
    
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]