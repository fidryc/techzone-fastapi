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
async def verify_email_code(request: Request, response: Response, code: int, session = Depends(get_session)):
    users_services = UserService(session)
    
    await users_services.confirm_email_and_register_user(request, response, code)


@router.post('/login')
async def login(response: Response, user: UserAuthSchema, session = Depends(get_session)):
    users_services = UserService(session)
    await users_services.auth_user(response, user)
    
    
@router.post('/logout')
async def login(response: Response, session = Depends(get_session)):
    users_services = UserService(session)
    users_services.logout_user(response)
    

@router.post('/delete_user')
async def delete_user(request: Request, response: Response, session = Depends(get_session)):
    users_services = UserService(session)
    user = await users_services.get_user_from_token(request, response)
    await users_services.delete_user(user, response)
    