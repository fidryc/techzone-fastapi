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