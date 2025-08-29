from aiosmtplib import send
import smtplib
from app.config import settings

async def async_send_email(msg_email):
    await send(msg_email,
               port=settings.SMTP_PORT,
               hostname=settings.SMTP_HOST,
               username=settings.SMTP_USER,
               password=settings.SMTP_PASS,
               use_tls=True)
    
def send_email(msg_email):
    try:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg_email)
    except:
        print('Произошла ошибка')
    finally:
        server.quit()