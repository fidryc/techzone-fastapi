from app.dao import BaseDao
from app.users.models import Users
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

class UsersDao(BaseDao):
    model = Users
    
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
            raise HTTPException(status_code=422, detail='Пользователь с такой почтой или номером телефона уже существует')
        return user_by_email
    
    async def find_user(self, email, number):
        user_by_email = await self.find_by_filter(email=email)
        user_by_number = await self.find_by_filter(number=number)
        if user_by_email:
            return user_by_email[0]
        if user_by_number:
            return user_by_number[0]
    
    
    
