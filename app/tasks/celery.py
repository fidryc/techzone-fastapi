import asyncio
from celery import Celery
from app.config import settings
from celery.schedules import crontab

app = Celery('tasks', broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}')

app.conf.beat_schedule = {
    'send_email_celery': {
        'task': 'app.tasks.tasks.update_product_index',
        'schedule': crontab(minute=0, hour=0),
        'args': ()
    },
}

app.conf.beat_schedule = {
    'send_email_celery': {
        'task': 'app.tasks.tasks.update_avg_reviews',
        'schedule': crontab(minute=0, hour=0),
        'args': ()
    },
}

