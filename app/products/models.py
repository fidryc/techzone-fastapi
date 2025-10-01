from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Float, Numeric, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class Category(Base):
    __tablename__ = 'categories'
   
    category_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(64))
    class_name: Mapped[str] = mapped_column(String(32))
   
class Product(Base):
    __tablename__ = 'products'
   
    product_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(256))
    category_id: Mapped[int | None] = mapped_column(ForeignKey('categories.category_id', ondelete='SET NULL'), index=True)
    specification: Mapped[dict] = mapped_column(JSONB)
    price: Mapped[float] = mapped_column(Numeric(10, 2), CheckConstraint('price >= 0'), index=True)
    rating: Mapped[float | None] = mapped_column(Float, CheckConstraint('rating > 0 and rating <= 5'), index=True)
    description: Mapped[str] = mapped_column(String(1024))
    months_warranty: Mapped[int | None] = mapped_column()
    country_origin: Mapped[str] = mapped_column(String(128))
    sale_percent: Mapped[int | None] = mapped_column(CheckConstraint('sale_percent >= 0 AND sale_percent <= 100'), default=0, index=True)
    views: Mapped[int | None] = mapped_column(CheckConstraint('views >= 0'))
   
    __table_args__ = (
        Index('idx_specification_gin', 'specification', postgresql_using='gin'),
    )
   
class Review(Base):
    __tablename__ = 'reviews'
   
    review_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    months_used: Mapped[int | None] = mapped_column()
    positive: Mapped[str | None] = mapped_column(String(512))
    negative: Mapped[str | None] = mapped_column(String(512))
    comment: Mapped[str] = mapped_column(String(1024))
    date_posted: Mapped[datetime | None] = mapped_column(default=datetime.now)
    date_updated: Mapped[datetime | None] = mapped_column(default=datetime.now, onupdate=datetime.now)
    is_edited: Mapped[bool | None] = mapped_column()
    rating: Mapped[int | None] = mapped_column(default=None)
   
class FavoriteProduct(Base):
    __tablename__ = 'favorite_products'
   
    favorite_product_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
   
   
class HistoryQueryUser(Base):
    '''История текстовых поисков продуктов пользователя'''
   
    __tablename__ = 'history_text_user'
   
    history_text_user_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    query_text: Mapped[int | None] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)