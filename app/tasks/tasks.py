from elasticsearch import Elasticsearch
from app.elasticsearch.services import ElasticsearchSyncService
from app.email.email_template import new_product_email, register_code
from app.email.servises import send_email
from app.tasks.celery import app
from celery import shared_task
from app.database import session_maker, session_maker_sync
from app.config import settings
from app.products.dao import ProductSyncDao, ReviewSyncDao


@app.task
def send_email_about_new_product(email, title, price):
    # для теста пока стоит мой email, поставить потом email
    email_msg = new_product_email('f98924746@gmail.com', title, price)
    send_email(email_msg)
    
@app.task
def update_product_index():
    """Реализовано через синхронные функции, тк celery не поддерживает асинхронность"""
    with Elasticsearch(hosts=f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}") as el_cl:
        el_service = ElasticsearchSyncService(el_cl)
        with session_maker_sync() as session:
            el_service.add_all_products(session=session)
    
@app.task
def update_avg_reviews():
    """Реализовано через синхронные функции, тк celery не поддерживает асинхронность"""
    with session_maker_sync() as session:
        review_dao = ReviewSyncDao(session)
        product_dao = ProductSyncDao(session)
        
        reviews = review_dao.rating_of_products()
        product_dao.update_avg_reviews(reviews)
        
        session.commit()
    
