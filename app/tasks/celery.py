from celery import Celery
from app.config import settings
from celery.schedules import crontab
import os
from celery.schedules import crontab
from app.redis.client import REDIS_URL

# Директория на уровень выше app
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BEAT_SCHEDULE_FILE = os.path.join(ROOT_DIR, 'celerybeat-schedule')

# :TODO Удаляем старый файл перед запуском
# if os.path.exists(BEAT_SCHEDULE_FILE):
#     os.remove(BEAT_SCHEDULE_FILE)
#     print(f"Deleted old beat schedule file: {BEAT_SCHEDULE_FILE}")

app: Celery = Celery('tasks', broker=REDIS_URL)

app.conf.timezone = 'Europe/Moscow'
app.conf.enable_utc = True  


app.conf.beat_schedule = {
    'update_avg_reviews': {
        'task': 'app.tasks.tasks.update_avg_reviews',
        'schedule': crontab(hour=0, minute=10),
        'args': ()
    },
    'update_product_index': {
        'task': 'app.tasks.tasks.update_product_index',
        'schedule': crontab(hour=0, minute=0),
        'args': ()
    }
}

