from elasticsearch.exceptions import ElasticsearchWarning, ConnectionError
from app.elasticsearch.elasticsearch_dao import ElasticsearchDao, ElasticsearchSyncDao
from app.products.dao import ProductDao, ProductSyncDao
from app.products.schema import ProductReturnSchema
from app.config import settings
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.logger import logger


class ElasticsearchService:
    def __init__(self, el_dao: ElasticsearchDao):
        self.el_dao = el_dao

    async def create_index_products(self):
        body = {
            "settings": {
                "index": {"max_ngram_diff": 12},
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "tokenizer": "ngram_tokenizer",
                            "filter": ["lowercase"]
                        }
                    },
                    "tokenizer": {
                        "ngram_tokenizer": {
                            "type": "ngram",
                            "min_gram": 3,
                            "max_gram": 15,
                            "token_chars": ["letter", "digit"]
                        }
                    }
                }
            },
            "mappings": {
                "dynamic": "false",
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "ngram_analyzer",
                        "search_analyzer": "standard"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "ngram_analyzer",
                        "search_analyzer": "standard"
                    }
                }
            }
        }
        
        try:
            await self.el_dao.create_index_with_body(index_name=settings.INDEX_PRODUCTS, body=body)
            logger.info('Products index created', extra={'index': settings.INDEX_PRODUCTS})
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Unexpected error creating products index', extra={'index': settings.INDEX_PRODUCTS}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при создании индекса продуктов'
            )
    
    async def add_all_products(self, session):
        try:
            product_dao = ProductDao(session)
            
            logger.debug('Checking if products index exists', extra={'index': settings.INDEX_PRODUCTS})
            if await self.el_dao.el_cl.indices.exists(index=settings.INDEX_PRODUCTS):
                logger.info('Deleting existing products index', extra={'index': settings.INDEX_PRODUCTS})
                await self.el_dao.delete_index(settings.INDEX_PRODUCTS)
                
            await self.create_index_products()
            
            rows = await product_dao.all()
            logger.info('Retrieved products for indexing', extra={'count': len(rows)})
            
            processed_docs = []
            for document in rows:
                document_json = ProductReturnSchema.model_validate(document, from_attributes=True).model_dump_json()
                processed_docs.append({
                    "_index": settings.INDEX_PRODUCTS,
                    "_source": document_json
                })
            
            await self.el_dao.add_documents(index_name=settings.INDEX_PRODUCTS, documents=processed_docs)
            logger.info('All products indexed successfully', extra={'count': len(processed_docs)})
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to add all products to index', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при индексации всех продуктов'
            )
        
    async def search_products(self, query_text):
        body = {
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": ["title^2", "description"],
                    "type": "best_fields"
                }
            }
        }
        try:
            logger.debug('Searching products', extra={'query': query_text})
            results = await self.el_dao.el_cl.search(index=settings.INDEX_PRODUCTS, body=body)
            hits_count = len(results.get('hits', {}).get('hits', []))
            logger.info('Products search completed', extra={'query': query_text, 'hits': hits_count})
            return results
        except ConnectionError as e:
            logger.error('Elasticsearch connection error', extra={'query': query_text}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Проблемы с подключением к ElasticSearch'
            )
        except ElasticsearchWarning as e:
            logger.error('Elasticsearch warning during search', extra={'query': query_text}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка ElasticSearch при поиске'
            )
        except Exception as e:
            logger.error('Unexpected error during product search', extra={'query': query_text}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при поиске продуктов'
            )


# Синхронный вариант для celery
class ElasticsearchSyncService:
    def __init__(self, el_cl):
        self.el_dao = ElasticsearchSyncDao(el_cl)

    def create_index_products(self):
        body = {
            "settings": {
                "index": {"max_ngram_diff": 12},
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "tokenizer": "ngram_tokenizer",
                            "filter": ["lowercase"]
                        }
                    },
                    "tokenizer": {
                        "ngram_tokenizer": {
                            "type": "ngram",
                            "min_gram": 3,
                            "max_gram": 15,
                            "token_chars": ["letter", "digit"]
                        }
                    }
                }
            },
            "mappings": {
                "dynamic": "false",
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "ngram_analyzer",
                        "search_analyzer": "standard"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "ngram_analyzer",
                        "search_analyzer": "standard"
                    }
                }
            }
        }
        
        try:
            self.el_dao.create_index_with_body(index_name=settings.INDEX_PRODUCTS, body=body)
            logger.info('Products index created (sync)', extra={'index': settings.INDEX_PRODUCTS})
        except Exception as e:
            logger.error('Failed to create products index (sync)', extra={'index': settings.INDEX_PRODUCTS}, exc_info=True)
            raise
    
    def add_all_products(self, session: Session):
        try:
            product_dao = ProductSyncDao(session)
            
            logger.debug('Checking if products index exists (sync)', extra={'index': settings.INDEX_PRODUCTS})
            if self.el_dao.el_cl.indices.exists(index=settings.INDEX_PRODUCTS):
                logger.info('Deleting existing products index (sync)', extra={'index': settings.INDEX_PRODUCTS})
                self.el_dao.delete_index(settings.INDEX_PRODUCTS)
                
            self.create_index_products()
            
            rows = product_dao.all()
            logger.info('Retrieved products for indexing (sync)', extra={'count': len(rows)})
            
            processed_docs = []
            for document in rows:
                document_json = ProductReturnSchema.model_validate(document, from_attributes=True).model_dump_json()
                processed_docs.append({
                    "_index": settings.INDEX_PRODUCTS,
                    "_source": document_json
                })
            
            self.el_dao.add_documents(index_name=settings.INDEX_PRODUCTS, documents=processed_docs)
            logger.info('All products indexed successfully (sync)', extra={'count': len(processed_docs)})
            
        except Exception as e:
            logger.error('Failed to add all products to index (sync)', exc_info=True)
            raise
        
    def search_products(self, query_text):
        body = {
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": ["title^2", "description"],
                    "type": "best_fields"
                }
            }
        }
        try:
            logger.debug('Searching products (sync)', extra={'query': query_text})
            results = self.el_dao.el_cl.search(index=settings.INDEX_PRODUCTS, body=body)
            logger.info('Products search completed (sync)', extra={'query': query_text})
            return results
        except Exception as e:
            logger.error('Failed to search products (sync)', extra={'query': query_text}, exc_info=True)
            raise