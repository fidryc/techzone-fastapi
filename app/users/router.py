from fastapi import APIRouter
from app.users.schema import UsersSchema
from app.users.servises import UsersServices
from fastapi import Depends, Response, Request
from app.database import get_session

router = APIRouter(
    prefix='/users',
    tags=['Пользователь']
)

@router.post('/register')
async def register(user: UsersSchema, session = Depends(get_session)):
    users_services = UsersServices(session)
    
    await users_services.add_user(user)
    
@router.post('/login')
async def login(response: Response, user: UsersSchema, session = Depends(get_session)):
    users_services = UsersServices(session)
    print('1')
    await users_services.auth_user(response, user)
    

@router.post('/test_jwt')
async def test_jwt(request: Request, response: Response, session = Depends(get_session)):
    users_services = UsersServices(session)
    user = await users_services.get_current_user(request, response)
    print(user.email)
    

@router.post('/refresh')
async def refresh(request: Request, response: Response, session = Depends(get_session)):
    users_services = UsersServices(session)
    user = await users_services.get_current_user(request, response)
    print(user.email)
    
    