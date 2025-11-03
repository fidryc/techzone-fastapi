from app.users.models import User
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Float, Numeric, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    class_name: Mapped[str] = mapped_column(String(32), nullable=False)


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    category_id: Mapped[int | None] = (
        mapped_column(  # 🧩 исправлено: ondelete='SET NULL' требует nullable=True
            ForeignKey("categories.category_id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        )
    )
    specification: Mapped[dict] = mapped_column(JSONB, nullable=False)
    price: Mapped[float] = mapped_column(
        Numeric(10, 2), CheckConstraint("price >= 0"), index=True, nullable=False
    )
    rating: Mapped[float | None] = mapped_column(
        Float, CheckConstraint("rating > 0 and rating <= 5"), index=True, nullable=True
    )
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    months_warranty: Mapped[int] = mapped_column(nullable=False)
    country_origin: Mapped[str] = mapped_column(String(128), nullable=False)
    sale_percent: Mapped[int | None] = mapped_column(
        CheckConstraint("sale_percent >= 0 AND sale_percent <= 100"),
        default=0,
        index=True,
        nullable=True,
    )
    views: Mapped[int | None] = mapped_column(
        CheckConstraint("views >= 0"), default=0, nullable=True
    )

    # relationship_category = relationship('Category', viewonly=True, lazy='joined')

    __table_args__ = (
        Index("idx_specification_gin", "specification", postgresql_using="gin"),
    )


class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    months_used: Mapped[int] = mapped_column(nullable=False)
    positive: Mapped[str] = mapped_column(String(512), nullable=False)
    negative: Mapped[str] = mapped_column(String(512), nullable=False)
    comment: Mapped[str] = mapped_column(String(1024), nullable=False)
    date_posted: Mapped[datetime | None] = mapped_column(
        default=datetime.now, nullable=True
    )
    date_updated: Mapped[datetime | None] = mapped_column(
        default=datetime.now, onupdate=datetime.now, nullable=True
    )
    is_edited: Mapped[bool] = mapped_column(default=False, nullable=False)
    rating: Mapped[int | None] = mapped_column(nullable=True)

    # relationship_user = relationship('User', viewonly=True, lazy='joined')
    # relationship_product = relationship('Product', viewonly=True, lazy='joined')


class FavoriteProduct(Base):
    __tablename__ = "favorite_products"

    favorite_product_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # relationship_user = relationship('User', viewonly=True, lazy='joined')
    # relationship_product = relationship('Product', viewonly=True, lazy='joined')

    def __repr__(self):
        return f"<FavoriteProduct {self.user_id=} {self.product_id=}>"


class HistoryQueryUser(Base):
    __tablename__ = "history_text_user"

    history_text_user_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    query_text: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # relationship_user = relationship('User', viewonly=True, lazy='joined')
