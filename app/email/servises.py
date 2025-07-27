from aiosmtplib import send
from app.config import settings

async def send_email(msg_email):
    await send(msg_email,
               port=settings.SMTP_PORT,
               hostname=settings.SMTP_HOST,
               username=settings.SMTP_USER,
               password=settings.SMTP_PASS,
               use_tls=True)