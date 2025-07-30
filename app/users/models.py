from app.database import Base

from sqlalchemy import Column, Integer, String


class Users(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=True, unique=True)
    hashed_password = Column(String)
    city = Column(String)
    home_address = Column(String)
    pickup_store = Column(String)
    number = Column(String, nullable=True, unique=True)
    
class RefreshTokenBL(Base):
    __tablename__ = 'refresh_token_bl'
    
    id = Column(Integer, primary_key=True, nullable=False)
    jti = Column(String, nullable=False, unique=True)