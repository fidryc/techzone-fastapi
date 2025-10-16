from fastapi import Request
from app.logger import logger
from datetime import datetime
from datetime import timezone

async def check_time(request: Request, call_next):
    start_time = datetime.now(timezone.utc)
    response = await call_next(request)
    logger.debug('Request execution time', extra={'total_seconds': (datetime.now(timezone.utc) - start_time).total_seconds()})
    return response