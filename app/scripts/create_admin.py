from app.database import session_maker
from sqlalchemy import insert, values
from app.users.models import User
from app.users.utils import get_hash

async def create_admin(email, pwd):
    try:
        async with session_maker() as session:
            query = insert(User).values(
                email=email,
                hashed_password=get_hash(pwd),
                role="admin"
                )
            await session.execute(query)
            await session.commit()
    except Exception:
        pass