from typing import Annotated

from fastapi import Depends
from app.elasticsearch.elasticsearch_dao import ElasticsearchDao
from app.elasticsearch.router import get_elasticsearch_cl
from app.elasticsearch.services import ElasticsearchService


def get_elasticsearch_dao(elasticsearch_cl = Depends(get_elasticsearch_cl)):
    return ElasticsearchDao(elasticsearch_cl)


def get_elasticsearch_service(el_dao = Depends(get_elasticsearch_dao)):
    return ElasticsearchService(el_dao)


ElasticsearchServiceDep = Annotated[ElasticsearchService, Depends(get_elasticsearch_service)]