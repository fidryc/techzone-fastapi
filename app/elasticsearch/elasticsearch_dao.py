from elasticsearch import AsyncElasticsearch, Elasticsearch
from elasticsearch.helpers import async_bulk, BulkIndexError, bulk
from elasticsearch.exceptions import ElasticsearchWarning
from app.logger import logger
from fastapi import HTTPException, status


class ElasticsearchDao:
    def __init__(self, el_cl: AsyncElasticsearch):
        self.el_cl = el_cl
       
    async def create_index_with_body(self, index_name: str, body: dict):
        try:
            await self.el_cl.indices.create(index=index_name, body=body)
            logger.info('Index created successfully', extra={'index': index_name})
        except ElasticsearchWarning as e:
            logger.error('Failed to create index', extra={'index': index_name}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ошибка при создании индекса {index_name}'
            )
    
    async def add_document(self, index_name: str, document: dict):
        try:
            await self.el_cl.index(index=index_name, document=document)
            logger.debug('Document added to index', extra={'index': index_name})
        except ElasticsearchWarning as e:
            logger.error('Failed to add document', extra={'index': index_name}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ошибка при добавлении документа в индекс {index_name}'
            )
       
    async def add_documents(self, index_name: str, documents: list[dict]):
        try:
            result = await async_bulk(self.el_cl, documents)
            logger.info('Documents added successfully', extra={'index': index_name, 'count': len(documents)})
            return result
        except BulkIndexError as e:
            failed_count = len(e.errors)
            logger.warning('Some documents failed to index', extra={
                'index': index_name,
                'total': len(documents),
                'failed': failed_count
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Не все документы были добавлены. Успешно: {len(documents) - failed_count}, Ошибок: {failed_count}'
            )
        except ElasticsearchWarning as e:
            logger.error('Failed to add documents', extra={'index': index_name, 'count': len(documents)}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при массовом добавлении документов'
            )
           
    async def delete_index(self, index_name: str):
        try:
            await self.el_cl.indices.delete(index=index_name)
            logger.info('Index deleted successfully', extra={'index': index_name})
        except ElasticsearchWarning as e:
            logger.error('Failed to delete index', extra={'index': index_name}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ошибка при удалении индекса {index_name}'
            )


# Синхронный вариант для celery
class ElasticsearchSyncDao:
    def __init__(self, el_cl):
        self.el_cl: Elasticsearch = el_cl
       
    def create_index_with_body(self, index_name: str, body: dict):
        try:
            self.el_cl.indices.create(index=index_name, body=body)
            logger.info('Index created successfully (sync)', extra={'index': index_name})
        except ElasticsearchWarning as e:
            logger.error('Failed to create index (sync)', extra={'index': index_name}, exc_info=True)
            raise
    
    def add_document(self, index_name: str, document: dict):
        try:
            self.el_cl.index(index=index_name, document=document)
            logger.debug('Document added to index (sync)', extra={'index': index_name})
        except ElasticsearchWarning as e:
            logger.error('Failed to add document (sync)', extra={'index': index_name}, exc_info=True)
            raise
       
    def add_documents(self, index_name: str, documents: list[dict]):
        try:
            result = bulk(self.el_cl, documents)
            logger.info('Documents added successfully (sync)', extra={'index': index_name, 'count': len(documents)})
            return result
        except BulkIndexError as e:
            failed_count = len(e.errors)
            logger.warning('Some documents failed to index (sync)', extra={
                'index': index_name,
                'total': len(documents),
                'failed': failed_count
            })
            raise
        except ElasticsearchWarning as e:
            logger.error('Failed to add documents (sync)', extra={'index': index_name, 'count': len(documents)}, exc_info=True)
            raise
           
    def delete_index(self, index_name: str):
        try:
            self.el_cl.indices.delete(index=index_name)
            logger.info('Index deleted successfully (sync)', extra={'index': index_name})
        except ElasticsearchWarning as e:
            logger.error('Failed to delete index (sync)', extra={'index': index_name}, exc_info=True)
            raise
        
    def index_exists(self, index):
        return self.el_cl.indices.exists(index=index)