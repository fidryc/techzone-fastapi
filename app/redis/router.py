from fastapi import APIRouter
from fastapi_cache.decorator import cache

from app.logger import logger

router = APIRouter(prefix="/redis", tags=["router for work with redis"])
