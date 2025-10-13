from app.email.email_template import courier_notification_msg
from app.tasks.celery_rbmq import app_rbmq
from app.email.servises import send_email
from app.logger import logger
from celery.exceptions import Reject

@app_rbmq.task
def send_courier_notification(courier_email, order_id, product_ids, quantity, address):
    try:
        msg = courier_notification_msg(courier_email, order_id, product_ids, quantity, address)
        send_email(msg)
    except Exception as e:
        logger.exception("Ошибка при отправке письма")
        raise Reject(e, requeue=False)