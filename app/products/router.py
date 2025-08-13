from fastapi import APIRouter, Depends, Query, Request, Response
from app.elasticsearch.router import get_elasticsearch_cl
from app.products.dao import ProductDao, ReviewDao
from app.products.schema import ProductSchema
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import get_session
from app.products.services import ProductService
from app.users.servises import UserService

from elasticsearch import AsyncElasticsearch
from app.elasticsearch.services import ElasticsearchService

router = APIRouter(
    prefix='/products',
    tags=['Работа с товарами']
)

@router.get('/search/{query_text}')
async def get_products(query_text: str, el_cl: AsyncElasticsearch = Depends(get_elasticsearch_cl)):
    el_service = ElasticsearchService(el_cl)
    return await el_service.search_products(query_text)


@router.get('/catalog/{category}/')
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
                                      country_origin = country_origin, specification_filters=specification_filters)
    
@router.post('/add')
async def add_product(request: Request, response: Response, product: ProductSchema, session=Depends(get_session)):
    user = await UserService(session).get_user_from_token(request, response)
    service = ProductService(session)
    
    await service.add_product(product, user)
    await session.commit()
    
@router.get('/recomendation', response_model=list[ProductSchema])
async def recomendation(request: Request, response: Response, session=Depends(get_session)):
    pass

@router.get('/all')
async def all(session=Depends(get_session)):
    product_dao = ProductDao(session)
    return await product_dao.all()
    
# @router.post('/add_job_reviews')
# async def add_job_reviews(scheduler=Depends(get_sheduler), session=Depends(get_session)):
#     product_service = ProductService(session)

        
@router.post('/update_reviews')
async def add_product(session=Depends(get_session)):
    service = ProductService(session)
    await service.update_ratings()