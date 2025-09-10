from app.database import Base
from sqlalchemy import CheckConstraint, Column, Enum, ForeignKey, JSON, DateTime, Index, Integer, Numeric, String
from datetime import datetime, timezone


class OrderType(Base):
    __tablename__ = 'order_types'
    
    order_type_id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(length=128))

class Order(Base):
    __tablename__ = 'orders'
    
    order_id = Column(Integer, primary_key=True, nullable=False)
    status = Column(Enum('new', 'confirmed', 'preparing', 'delivered', 'ready', 'finished', 'cancelled', name='order_status_enum'), nullable=False)
    order_type_id = Column(ForeignKey('order_types.order_type_id', ondelete='RESTRICT'))
    order_detail_id = Column(Integer) 
    user_id = Column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    date = Column(DateTime, default=datetime.now(timezone.utc), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=True)
    
    
class OrderPickUpDetail(Base):
    __tablename__ = 'order_pickup_details'
    
    order_pickup_detail_id = Column(Integer, primary_key=True, nullable=False)
    store_id = Column(ForeignKey('stores.store_id', ondelete='CASCADE'), nullable=False, index=True)
    
class OrderDeliveryDetail(Base):
    __tablename__ = 'order_delivery_details'
    
    order_delivery_detail_id = Column(Integer, primary_key=True, nullable=False)
    address = Column(String(length=128), nullable=False)

    
class Purchase(Base):
    __tablename__ = 'purchases'
    
    purchase_id = Column(Integer, primary_key=True, nullable=False)
    order_id = Column(ForeignKey('orders.order_id', ondelete='CASCADE'), index=True)
    product_id = Column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    
class Basket(Base):
    __tablename__ = 'baskets'
    
    basket_id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    product_id = Column(ForeignKey('products.product_id', ondelete='CASCADE'))
    