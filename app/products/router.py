import functools
from fastapi import APIRouter, Depends, Query, Request, Response
from app.elasticsearch.router import get_elasticsearch_cl
from app.products.dao import ProductDao, ProductSyncDao, ReviewDao
from app.products.schema import ProductSchema
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import get_session, get_session_sync
from app.products.services import ProductService
from app.tasks.tasks import send_email_about_new_product
from app.users.servises import UserService

from elasticsearch import AsyncElasticsearch
from app.elasticsearch.services import ElasticsearchService
from fastapi_cache.decorator import cache

from datetime import datetime

from app.database import session_maker_sync

router = APIRouter(
    prefix='/products',
    tags=['Работа с товарами']
)

@router.get('/search/{query_text}')
@cache(expire=180)
async def get_products(query_text: str, el_cl: AsyncElasticsearch = Depends(get_elasticsearch_cl)):
    el_service = ElasticsearchService(el_cl)
    return await el_service.search_products(query_text)

@router.get('/catalog/{category}/')
@cache(expire=180)
async def get_products(
    category: str,
    price: str = Query(None),
    rating: float = Query(None),
    months_warranty: int = Query(None),
    country_origin: str = Query(None),
    session = Depends(get_session),
    request: Request = None,
    ):
    def_par = {'category', 'price', 'rating', 'months_warranty', 'country_origin'}
    specification_filters = {k: el for k, el in request.query_params.items() if k not in def_par}
    dao = ProductDao(session)
    return await dao.get_with_filters(category = category,
                                      price = price,
                                      rating = rating,
                                      months_warranty = months_warranty,
                                      country_origin = country_origin,
                                      specification_filters=specification_filters)
    
@router.post('/add_product')
async def add_product(request: Request, response: Response, product: ProductSchema, session=Depends(get_session)):
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    product_service = ProductService(session)
    
    await product_service.add_product(product, user, flag_notification=True)
    await session.commit()
    
@router.post('/')
async def add_product(request: Request, response: Response, product: ProductSchema, session=Depends(get_session)):
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    product_service = ProductService(session)
    
    await product_service.add_product(product, user, flag_notification=True)
    await session.commit()
    
@router.get('/recomendation', response_model=list[ProductSchema])
@cache(expire=30)
async def recomendation(request: Request, response: Response, session=Depends(get_session)):
    user = await UserService(session).get_user_from_token(request, response)
    product_service = ProductService(session)
    return await product_service.recomendation(user.user_id)

@router.get('/all')
async def all(session=Depends(get_session)):
    product_dao = ProductDao(session)
    return await product_dao.all()

    
@router.post('/find_by_id')
async def add_product(product_id: int, session=Depends(get_session)):
    service = ProductService(session)
    return await service.product_dao.find_by_id(product_id)
