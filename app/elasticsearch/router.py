from fastapi import Request
from fastapi import APIRouter, Depends
from elasticsearch import AsyncElasticsearch, Elasticsearch

from app.database import get_session
from app.elasticsearch.config import ELASTICSEARCH_URL
from app.elasticsearch.elasticsearch_dao import ElasticsearchDao
from app.products.dao import ProductDao
from app.products.schema import ProductReturnSchema, ProductSchema

from app.elasticsearch.services import ElasticsearchService, ElasticsearchSyncService
from app.config import settings
from app.database import session_maker_sync
router = APIRouter(
    prefix='/el',
    tags=['el']
)

def get_elasticsearch_cl(request: Request):
    """Dependency для получения сервиса Elasticsearch"""
    return request.app.state.el_cl

def get_elasticsearch_cl_sync(request: Request):
    """Dependency для получения сервиса Elasticsearch"""
    return request.app.state.el_cl_sync

@router.post('/delete_index')
async def create_index(index_name:str, el_cl: AsyncElasticsearch=Depends(get_elasticsearch_cl)):
    el_dao = ElasticsearchDao(el_cl)
    el_service = ElasticsearchService(el_dao)
    await el_service.el_dao.delete_index(index_name)

@router.post('/create_index')
async def create_index(index_name:str, body: dict, el_cl: AsyncElasticsearch=Depends(get_elasticsearch_cl)):
    el_dao = ElasticsearchDao(el_cl)
    el_service = ElasticsearchService(el_dao)
    await el_service.el_dao.create_index_with_body(index_name=index_name, body=body)

@router.post('/add_document')
async def add_document(index_name:str, document: dict, el_cl: AsyncElasticsearch=Depends(get_elasticsearch_cl)):
    pass
   
@router.post('/create_index_products')
async def create_index_products(el_cl: AsyncElasticsearch=Depends(get_elasticsearch_cl)):
    el_dao = ElasticsearchDao(el_cl)
    el_service = ElasticsearchService(el_dao)
    await el_service.create_index_products()
    
@router.post('/add_all_products')
async def add_all_products(el_cl: AsyncElasticsearch=Depends(get_elasticsearch_cl), session=Depends(get_session)):
    el_dao = ElasticsearchDao(el_cl)
    el_service = ElasticsearchService(el_dao)
    await el_service.add_all_products(session)
    
@router.post('/add_all_products_sync')
def add_all_products():
    with Elasticsearch(hosts=ELASTICSEARCH_URL) as el_cl:
        el_service = ElasticsearchSyncService(el_cl)
        with session_maker_sync() as session:
            el_service.add_all_products(session=session)