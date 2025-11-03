from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from app.elasticsearch.config import ELASTICSEARCH_URL
from app.elasticsearch.services import ElasticsearchSyncService
from app.products.services import ProductServiceSync
from app.tasks.celery import app
from app.database import session_maker_sync
from app.products.dao import ProductSyncDao, ReviewSyncDao
from app.logger import logger


@app.task
def update_product_index():
    """Обновление индекса продуктов в elasticsearch"""
    try:
        logger.info("Starting product index update task")
        with Elasticsearch(hosts=ELASTICSEARCH_URL) as el_cl:
            el_service = ElasticsearchSyncService(el_cl)
            with session_maker_sync() as session:
                el_service.add_all_products(session)
        logger.info("Product index update completed successfully")
    except ConnectionError as e:
        logger.error("Elasticsearch error during index update", exc_info=True)
        raise
    except Exception as e:
        logger.error("Failed to update product index", exc_info=True)
        raise


@app.task
def update_avg_reviews():
    """Обновление средних оценок у продуктов"""
    try:
        logger.info("Starting average reviews update task")
        with session_maker_sync() as session:
            logger.debug("Opened sync session for reviews update")
            review_dao = ReviewSyncDao(session)
            product_dao = ProductSyncDao(session)
            ProductServiceSync(product_dao, review_dao).update_reviews()

            session.commit()
            logger.info("Average reviews update completed successfully")
    except Exception as e:
        logger.error("Failed to update average reviews", exc_info=True)
        raise
