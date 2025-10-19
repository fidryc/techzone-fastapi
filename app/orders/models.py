from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Numeric, Enum
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class OrderType(Base):
    __tablename__ = 'order_types'

    order_type_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)


class Order(Base):
    __tablename__ = 'orders'

    order_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(Enum('new', 'confirmed', 'preparing', 'delivered', 'ready', 'finished', 'cancelled', name='order_status_enum'), nullable=False)
    order_type_id: Mapped[int] = mapped_column(ForeignKey('order_types.order_type_id', ondelete='RESTRICT'), nullable=False)
    order_detail_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    date: Mapped[datetime | None] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True
    )
    
    relationship_user = relationship('User', back_populates='relationship_orders')


class OrderPickUpDetail(Base):
    __tablename__ = 'order_pickup_details'

    order_pickup_detail_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey('stores.store_id', ondelete='CASCADE'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True, nullable=False)

    relationship_store = relationship('Store')
    relationship_user = relationship('User')

class OrderDeliveryDetail(Base):
    __tablename__ = 'order_delivery_details'

    order_delivery_detail_id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True, nullable=False)

    relationship_user = relationship('User')

class Purchase(Base):
    __tablename__ = 'purchases'

    purchase_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.order_id', ondelete='CASCADE'), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.product_id', ondelete='RESTRICT'), index=True, nullable=False)

    relationship_order = relationship('Order')
    relationship_product = relationship('Product')
    
    
class Basket(Base):
    __tablename__ = 'baskets'

    basket_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)

    relationship_user = relationship('User')
    relationship_product = relationship('Product')