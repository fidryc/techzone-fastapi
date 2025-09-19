from app.dao import BaseDao
from app.exceptions import HttpExc409Conflict
from app.users.models import User, RefreshTokenBL
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import text

class UserDao(BaseDao):
    model = User
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        
    async def check_user(self, email, number):
        user_by_email = None
        user_by_number = None
        if email:
            user_by_email = await self.find_by_filter(email=email)
        if number:
            user_by_number = await self.find_by_filter(number=number)
        
        if user_by_email or user_by_number:
            raise HttpExc409Conflict('Пользователь с такой почтой или номером телефона уже существует')
        return user_by_email
    
    
    async def find_user(self, email, number):
        user_by_email = await self.find_by_filter(email=email)
        user_by_number = await self.find_by_filter(number=number)
        if user_by_email:
            return user_by_email[0]
        if user_by_number:
            return user_by_number[0]
    
    
    async def delete_user(self, user_id: int):
        query = text('''
        DELETE FROM users
        WHERE user_id = :user_id
        ''')
        await self.session.execute(query, params={'user_id': user_id})
        


class RefreshTokenBLDao(BaseDao):
    model = RefreshTokenBL
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_reftoken_bl(self, jti):
        token = await self.find_by_filter(jti=jti)
        return token
    
    