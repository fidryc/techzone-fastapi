from app.email.email_template import new_product_email, register_code
from app.email.services import send_email
from app.tasks.celery import app
from app.logger import logger


@app.task
def send_email_about_new_product(email, title, price):
    """Отправка писем о появлении нового продукта"""
    # для теста пока стоит мой email, поставить потом email
    email_msg = new_product_email("f98924746@gmail.com", title, price)
    send_email(email_msg)


@app.task
def send_email_code(email, code):
    """Отправка письма с кодом подверждения"""
    # для теста пока стоит мой email, поставить потом email
    email_msg = register_code("f98924746@gmail.com", code)
    send_email(email_msg)
    logger.debug("Send registration code")
