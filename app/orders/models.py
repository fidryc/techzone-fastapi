from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum, ForeignKey, Numeric, String
from datetime import datetime, timezone

class OrderType(Base):
    __tablename__ = 'order_types'
   
    order_type_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(128))

class Order(Base):
    __tablename__ = 'orders'
   
    order_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(Enum('new', 'confirmed', 'preparing', 'delivered', 'ready', 'finished', 'cancelled', name='order_status_enum'))
    order_type_id: Mapped[int | None] = mapped_column(ForeignKey('order_types.order_type_id', ondelete='RESTRICT'))
    order_detail_id: Mapped[int | None] = mapped_column()
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    date: Mapped[datetime | None] = mapped_column(default=lambda: datetime.now(timezone.utc))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime | None] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
   
   
class OrderPickUpDetail(Base):
    __tablename__ = 'order_pickup_details'
   
    order_pickup_detail_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int | None] = mapped_column(ForeignKey('stores.store_id', ondelete='CASCADE'), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
   
   
class OrderDeliveryDetail(Base):
    __tablename__ = 'order_delivery_details'
   
    order_delivery_detail_id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)

class Purchase(Base):
    __tablename__ = 'purchases'
   
    purchase_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey('orders.order_id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.product_id', ondelete='RESTRICT'), index=True)
   
   
class Basket(Base):
    __tablename__ = 'baskets'
   
    basket_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'))