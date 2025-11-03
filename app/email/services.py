from aiosmtplib import send, SMTPException
import smtplib
from app.config import settings
from app.logger import logger
from fastapi import HTTPException, status


async def async_send_email(msg_email):
    """Асинхронная отправка email"""
    recipient = msg_email.get('To', 'unknown')
    try:
        await send(
            msg_email,
            port=settings.SMTP_PORT,
            hostname=settings.SMTP_HOST,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=True
        )
        logger.info('Email sent successfully (async)', extra={'recipient': recipient})
    except SMTPException as e:
        logger.error('SMTP error sending email (async)', extra={'recipient': recipient}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка SMTP при отправке email'
        )
    except Exception as e:
        logger.error('Unexpected error sending email (async)', extra={'recipient': recipient}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Непредвиденная ошибка при отправке email'
        )

    
def send_email(msg_email):
    """Синхронная отправка email (для Celery)"""
    server = None
    recipient = msg_email.get('To', 'unknown')
    try:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg_email)
        logger.info('Email sent successfully (sync)', extra={'recipient': recipient})
    except smtplib.SMTPException as e:
        logger.error('SMTP error sending email (sync)', extra={'recipient': recipient}, exc_info=True)
        raise
    except Exception as e:
        logger.error('Unexpected error sending email (sync)', extra={'recipient': recipient}, exc_info=True)
        raise
    finally:
        if server:
            try:
                server.quit()
                logger.debug('SMTP connection closed')
            except Exception as e:
                logger.warning('Failed to close SMTP connection', exc_info=True)