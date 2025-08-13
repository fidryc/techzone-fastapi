from app.database import session_maker
from sqlalchemy import insert, values, select
from sqlalchemy.ext.asyncio import AsyncSession


class Pass:
    pass

class BaseDao:
    model = Pass
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, **data):
        query = insert(self.model).values(**data)
        await self.session.execute(query)
            
    async def find_by_id(self, id):
        query = select(self.model).filter_by(id=id)
        obj = await self.session.execute(query)
        return obj.scalar_one_or_none()
        
    async def find_by_filter(self, **filters):
        query = select(self.model).filter_by(**filters)
        obj = await self.session.execute(query)
        return obj.scalars().all()
    
    async def find_by_filter_one(self, **filters):
        query = select(self.model).filter_by(**filters)
        obj = await self.session.execute(query)
        return obj.scalar_one_or_none()
    
    async def all(self):
        query = select(self.model)
        obj = await self.session.execute(query)
        return obj.scalars().all()