from app.database import Base

from sqlalchemy import Column, Enum, Integer, String, ForeignKey


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)
    hashed_password = Column(String)
    city = Column(String)
    home_address = Column(String)
    pickup_store_id = Column(ForeignKey('stores.store_id', ondelete='SET NULL'), nullable=True, default=None)
    number = Column(String, nullable=True, unique=True)
    role = Column(Enum('user', 'seller', 'admin', name='user_role_enum'), default='user', nullable=False)
    
class RefreshTokenBL(Base):
    __tablename__ = 'refresh_token_bl'
    
    refresh_token_bl_id = Column(Integer, primary_key=True, nullable=False)
    jti = Column(String, nullable=False, unique=True)
    
