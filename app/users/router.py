from datetime import datetime, timedelta
from fastapi import APIRouter
from app.email.email_template import register_code
from app.email.servises import send_email
from app.users.schema import UserAuthSchema, UserSchema
from app.users.servises import UserService
from fastapi import Depends, Response, Request
from app.database import get_session

router = APIRouter(
    prefix='/users',
    tags=['Пользователь']
)

@router.post('/register')
async def register(response: Response, user: UserSchema, session = Depends(get_session)):
    users_services = UserService(session)
    
    await users_services.create_user_with_verification(response, user)
    
@router.post('/verify_email_code')
async def verify_email_code(request: Request, code: int, session = Depends(get_session)):
    users_services = UserService(session)
    
    await users_services.confirm_email_and_register_user(request, code)
    await session.commit()
    
@router.post('/login')
async def login(response: Response, user: UserAuthSchema, session = Depends(get_session)):
    users_services = UserService(session)
    await users_services.auth_user(response, user)
    
@router.post('/logout')
async def login(response: Response, session = Depends(get_session)):
    users_services = UserService(session)
    users_services.logout_user(response)
    

@router.post('/test_jwt')
async def test_jwt(request: Request, response: Response, session = Depends(get_session)):
    users_services = UserService(session)
    user = await users_services.get_user_from_token(request, response)
    return user.user_id
    

@router.post('/refresh')
async def refresh(request: Request, response: Response, session = Depends(get_session)):
    users_services = UserService(session)
    user = await users_services.get_current_user(request, response)
    
    
@router.post('/test_email')
def test():
    msg = register_code('f98924746@gmail.com', '123')
    send_email(msg)
    