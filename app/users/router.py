from fastapi import APIRouter
from app.users.schema import UsersAuthSchema, UsersSchema
from app.users.servises import UsersServices
from fastapi import Depends, Response, Request
from app.database import get_session

router = APIRouter(
    prefix='/users',
    tags=['Пользователь']
)

@router.post('/register')
async def register(response: Response, user: UsersSchema, session = Depends(get_session)):
    users_services = UsersServices(session)
    
    await users_services.create_user_with_verification(response, user)
    
@router.post('/verify_email_code')
async def verify_email_code(request: Request, code: int, session = Depends(get_session)):
    users_services = UsersServices(session)
    
    await users_services.confirm_email_and_register_user(request, code)
    await session.commit()
    
@router.post('/login')
async def login(response: Response, user: UsersAuthSchema, session = Depends(get_session)):
    users_services = UsersServices(session)
    await users_services.auth_user(response, user)
    
@router.post('/logout')
async def login(response: Response, session = Depends(get_session)):
    users_services = UsersServices(session)
    users_services.logout_user(response)
    

@router.post('/test_jwt')
async def test_jwt(request: Request, response: Response, session = Depends(get_session)):
    users_services = UsersServices(session)
    user = await users_services.get_user_from_token(request, response)
    

@router.post('/refresh')
async def refresh(request: Request, response: Response, session = Depends(get_session)):
    users_services = UsersServices(session)
    user = await users_services.get_current_user(request, response)
    
    