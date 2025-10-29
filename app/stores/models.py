from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

class Store(Base):
    __tablename__ = 'stores'

    store_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(56), nullable=False)
    opening_hours: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # relationship_user = relationship('User', back_populates='relationship_store')

class StoreQuantityInfo(Base):
    __tablename__ = 'stores_quantity_info'

    stores_quantity_info_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey('stores.store_id', ondelete='CASCADE'), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.product_id', ondelete='CASCADE'), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(CheckConstraint('quantity >= 0'), nullable=False)
    
    # relationship_store = relationship('Store')
    # relationship_product = relationship('Product')