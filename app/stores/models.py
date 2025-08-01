from app.database import Base
from sqlalchemy import CheckConstraint, Column, String, Integer, JSON, ForeignKey, Float, DateTime, Boolean
from datetime import datetime

class Store(Base):
    __tablename__ = 'stores'
    
    store_id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(length=56), nullable=False)
    opening_hours = Column(String(length=128), nullable=False)
    
class StoreQuantityInfo(Base):
    __tablename__ = 'stores_quantity_info'
    
    stores_quantity_info_id = Column(Integer, primary_key=True, nullable=False)
    store_id = Column(ForeignKey('stores.store_id', ondelete='CASCADE'), index=True)
    product_id = Column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    quantity = Column(Integer, CheckConstraint('quantity >= 0'))