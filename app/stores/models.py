from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import CheckConstraint, String, ForeignKey

class Store(Base):
    __tablename__ = 'stores'
   
    store_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(56))
    opening_hours: Mapped[str] = mapped_column(String(128))
   
class StoreQuantityInfo(Base):
    __tablename__ = 'stores_quantity_info'
   
    stores_quantity_info_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int | None] = mapped_column(ForeignKey('stores.store_id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True)
    quantity: Mapped[int | None] = mapped_column(CheckConstraint('quantity >= 0'))