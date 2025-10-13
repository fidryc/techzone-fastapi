from celery import Celery
from celery.exceptions import Reject
from kombu import Queue, Exchange
import logging
from app.config import settings
from app.email.email_template import courier_notification_msg
from app.email.servises import send_email

app_rbmq = Celery(
    'tasks_rbmq',
    broker=f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//'
)

default_exchange = Exchange('order_formation_exchange', type='direct', durable=True)
dlx_exchange = Exchange('dead_letter_exchange', type='direct', durable=True)

app_rbmq.conf.update(
    task_queues=(
        Queue(
            'send_mail_order_formation',
            exchange=default_exchange,
            routing_key='send_mail',
            durable=True,
            queue_arguments={
                'x-dead-letter-exchange': 'dead_letter_exchange',
                'x-dead-letter-routing-key': 'dead-letter',
            }
        ),
        Queue(
            'dead_letter_queue',
            exchange=dlx_exchange,
            routing_key='dead-letter',
            durable=True,
        ),
    ),
    task_routes={
        'app.tasks.tasks_rbmq.send_courier_notification': {
            'queue': 'send_mail_order_formation',
            'routing_key': 'send_mail'
        },
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_max_retries=0,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)
