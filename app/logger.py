from datetime import datetime, timezone
import logging
from pythonjsonlogger import jsonlogger
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

logger = logging.getLogger(__name__)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")

logHandler = logging.StreamHandler()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(settings.LOG_LEVEL)


def create_msg_db_error(e, optinal_info=None) -> str:
    """
    Возвращает сообщение для ошибки связанной с бд, добавляет дополнительную информацию.
    Если ошибка не связана с бд, то возвращает другое сообщение
    """
    
    if isinstance(e, SQLAlchemyError):
        msg = "Database exception"
        if optinal_info:
            msg += ": " + optinal_info
    elif isinstance(e, Exception):
        msg = "Unknow exception"
