from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum, String, ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str | None] = mapped_column(nullable=True)
    home_address: Mapped[str | None] = mapped_column(nullable=True)
    pickup_store_id: Mapped[int | None] = mapped_column(
        ForeignKey('stores.store_id', ondelete='SET NULL'),
        default=None,
        nullable=True
    )
    number: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    role: Mapped[str] = mapped_column(
        Enum('user', 'seller', 'admin', name='user_role_enum'),
        default='user',
        nullable=False
    )
    
    relationship_orders = relationship('Order', back_populates='relationship_user')
    relationship_store = relationship('Store', back_populates='relationship_user')
    
    
class RefreshTokenBL(Base):
    __tablename__ = 'refresh_token_bl'

    refresh_token_bl_id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(unique=True, nullable=False)