from app.database import Base
from sqlalchemy import Column, Index, String, Integer, ForeignKey, Float, DateTime, Boolean, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class Category(Base):
    __tablename__ = 'categories'
    
    category_id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(length=64))
    class_name = Column(String(length=32), nullable=False)
    
class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(length=256))
    category_id = Column(ForeignKey(column='categories.category_id', ondelete='SET NULL'), nullable=True, index=True)
    specification = Column(JSONB, nullable=False)
    price = Column(Numeric(10, 2), CheckConstraint('price >= 0'), nullable=False)
    rating = Column(Float, CheckConstraint('rating > 0 and rating <= 5'), nullable=True)
    description = Column(String(1024), nullable=False)
    months_warranty = Column(Integer, nullable=True)
    country_origin = Column(String(length=128), nullable=False)
    sale_percent = Column(Integer, CheckConstraint('sale_percent >= 0 AND sale_percent <= 100'), nullable=True, default=0)
    views = Column(Integer, CheckConstraint('views >= 0'))
    
    __table_args__ = (
        Index('idx_specification_gin', 'specification', postgresql_using='gin'),
    )
    
class Review(Base):
    __tablename__ = 'reviews'
    
    review_id = Column(Integer, primary_key=True, nullable=False)
    product_id = Column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    user_id = Column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    months_used = Column(Integer)
    positive = Column(String(length=512), nullable=True)
    negative = Column(String(length=512), nullable=True)
    comment = Column(String(1024), nullable=False)
    date_posted = Column(DateTime, default=datetime.now())
    date_updated = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_edited = Column(Boolean)
    
class FavoriteProduct(Base):
    __tablename__ = 'favorite_products'
    
    favorite_product_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    product_id = Column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    
class Basket(Base):
    __tablename__ = 'baskets'
    
    basket_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    product_id = Column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    quantity = Column(Integer, CheckConstraint('quantity >= 0'))

    