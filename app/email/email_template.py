from email.message import EmailMessage
from app.config import settings

def register_code(email_to, code):
    email_message = EmailMessage()
    email_message['Subject'] = 'Уведомление о регистрации на techzone'
    email_message['From'] = settings.SMTP_USER
    email_message['To'] = email_to
    
    email_message.set_content(
        f"""
        <h1>Вы пытаетесь зарегистрироваться на techzone</h1>
        Подвердите почту введя код: {code}
        """,
        subtype='html'
    )
    return email_message

def new_product_email(email_to, title, price):
    email_message = EmailMessage()
    email_message['Subject'] = 'Уведомление о появлении нового продукта на techzone'
    email_message['From'] = settings.SMTP_USER
    email_message['To'] = email_to
    
    email_message.set_content(
        f"""
        <h1>Новый товар вашей любимой категории на techzone</h1>
        Возможно вам понравится новый товар {title} по цене {price}
        """,
        subtype='html'
    )
    return email_message

def courier_notification_msg(email_to: str, order_id: int, product_ids: list[int], quantity: list[int], address: str):
    email_message = EmailMessage()
    1 / 0
    email_message['subject'] = 'Доставка заказа'
    email_message['From'] = settings.SMTP_USER
    email_message['To'] = email_to
    s = f'<h1>Доставить заказ номер {order_id} по адресу {address}</h1>\n'
    for i in range(len(product_ids)):
        s += f'Товар с id {product_ids[i]} в количестве {quantity[i]}<br>'
        
    email_message.set_content(s, subtype='html')
    print(email_message)
    return email_message
    