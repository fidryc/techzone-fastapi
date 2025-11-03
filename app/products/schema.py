from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, Field
from typing import Optional
from json import dumps


class ProductSchema(BaseModel):
    title: str
    category_id: int
    specification: dict
    price: float
    rating: Optional[float] = None
    description: str
    months_warranty: int
    country_origin: str
    sale_percent: Optional[int] = None
    views: Optional[int] = None


class ProductResponseSchema(BaseModel):
    product_id: int
    title: str
    category_id: int
    specification: dict
    price: float
    rating: Optional[float] = None
    description: str
    months_warranty: int
    country_origin: str
    sale_percent: Optional[int] = None
    views: Optional[int] = None


class ProductReturnSchema(BaseModel):
    product_id: int
    title: str
    category_id: int
    specification: dict
    price: float
    rating: Optional[float] = None
    description: str
    months_warranty: int
    country_origin: str
    sale_percent: Optional[int] = None
    views: Optional[int] = None


class HistoryQueryUserSchema(BaseModel):
    history_text_user_id: int
    user_id: int
    query_text: str
