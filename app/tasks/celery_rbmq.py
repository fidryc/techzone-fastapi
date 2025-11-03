from celery import Celery
from kombu import Queue, Exchange
from app.config import settings

if settings.MODE == "DEV":
    RABBITMQ_URL = f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
elif settings.MODE == "PROD":
    RABBITMQ_URL = f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST_PROD}:{settings.RABBITMQ_PORT}//"
elif settings.MODE == "TEST":
    RABBITMQ_URL = f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST_PROD}:{settings.RABBITMQ_PORT}//"


app_rbmq = Celery("tasks_rbmq", broker=RABBITMQ_URL)

default_exchange = Exchange("order_formation_exchange", type="direct", durable=True)
dlx_exchange = Exchange("dead_letter_exchange", type="direct", durable=True)

app_rbmq.conf.update(
    task_queues=(
        Queue(
            "send_mail_order_formation",
            exchange=default_exchange,
            routing_key="send_mail",
            durable=True,
            queue_arguments={
                "x-dead-letter-exchange": "dead_letter_exchange",
                "x-dead-letter-routing-key": "dead-letter",
            },
        ),
        Queue(
            "dead_letter_queue",
            exchange=dlx_exchange,
            routing_key="dead-letter",
            durable=True,
        ),
    ),
    task_routes={
        "app.tasks.tasks_rbmq.send_courier_notification": {
            "queue": "send_mail_order_formation",
            "routing_key": "send_mail",
        },
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_max_retries=0,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
