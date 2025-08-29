from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import bulk
from app.elasticsearch.elasticsearch_dao import ElasticsearchDao, ElasticsearchSyncDao
from app.products.dao import ProductDao, ProductSyncDao
from app.products.schema import ProductReturnSchema
from app.config import settings

class ElasticsearchService:
    def __init__(self, el_cl):
        self.el_dao = ElasticsearchDao(el_cl)

    async def create_index_products(self):
        body = {
        "settings": {
            "index": {
            "max_ngram_diff": 12
            },
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
        
        await self.el_dao.create_index_with_body(index_name=settings.INDEX_PRODUCTS, body=body)
    
    async def add_all_products(self, session):
        product_dao = ProductDao(session)
        
        if await self.el_dao.el_cl.indices.exists(index=settings.INDEX_PRODUCTS):
            await self.el_dao.delete_index(settings.INDEX_PRODUCTS)
            
        await self.create_index_products()
        
        processed_docs = []
        rows = await product_dao.all()
        for document in rows:
            document_json = ProductReturnSchema.model_validate(document, from_attributes=True).model_dump_json()
            processed_docs.append(
                {
                    "_index": settings.INDEX_PRODUCTS,
                    "_source": document_json
                }
            )
            
        await self.el_dao.add_documents(index_name=settings.INDEX_PRODUCTS, documents=processed_docs)
        
        
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
        return await self.el_dao.el_cl.search(index=settings.INDEX_PRODUCTS, body=body)
    
# Синхронный вариант для celery
class ElasticsearchSyncService:
    def __init__(self, el_cl):
        self.el_dao = ElasticsearchSyncDao(el_cl)

    def create_index_products(self):
        body = {
        "settings": {
            "index": {
            "max_ngram_diff": 12
            },
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
        
        self.el_dao.create_index_with_body(index_name=settings.INDEX_PRODUCTS, body=body)
    
    def add_all_products(self, session):
        product_dao = ProductSyncDao(session)
        
        if self.el_dao.el_cl.indices.exists(index=settings.INDEX_PRODUCTS):
            self.el_dao.delete_index(settings.INDEX_PRODUCTS)
            
        self.create_index_products()
        
        processed_docs = []
        rows = product_dao.all()
        for document in rows:
            document_json = ProductReturnSchema.model_validate(document, from_attributes=True).model_dump_json()
            processed_docs.append(
                {
                    "_index": settings.INDEX_PRODUCTS,
                    "_source": document_json
                }
            )
            
        self.el_dao.add_documents(index_name=settings.INDEX_PRODUCTS, documents=processed_docs)
        
        
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
        return self.el_dao.el_cl.search(index=settings.INDEX_PRODUCTS, body=body)