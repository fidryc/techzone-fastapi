from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk, BulkIndexError


class ElasticsearchDao:
    def __init__(self, el_cl):
        self.el_cl: AsyncElasticsearch = el_cl
        
    async def create_index_with_body(self, index_name:str, body: dict):
        await self.el_cl.indices.create(index=index_name, body=body)

    async def add_document(self, index_name:str, document: dict):
        await self.el_cl.index(index=index_name, document=document)
        
    async def add_documents(self, index_name:str, documents: list[dict]):
        try:
            result = await async_bulk(self.el_cl, documents)
        except BulkIndexError as e:
            print('не все документы были добавлены. Ошибка {e}')
            
    async def delete_index(self, index_name: str):
        await self.el_cl.indices.delete(index=index_name)
        