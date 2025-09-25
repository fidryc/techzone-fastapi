from datetime import datetime, timedelta
from fastapi import APIRouter, Path
from app.email.email_template import register_code
from app.email.servises import send_email
from app.users.depends import CurrentUserDep, UserServiceDep
from app.users.schema import UserAuthEmailSchema, UserAuthNumberSchema, UserRegisterEmailSchema, UserRegisterNumberSchema, UserSchema
from app.users.services import UserService
from fastapi import Depends, Response, Request
from app.database import get_session

router = APIRouter(
    prefix='/users',
    tags=['Пользователь']
)
    
    
@router.post('/register_with_email')
async def register_with_email(request: Request, response: Response, user: UserRegisterEmailSchema, user_service: UserServiceDep):
    await user_service.create_user_with_verification(request, response, user)
    
    
@router.post('/register_with_number')
async def register_with_number(request: Request, response: Response, user: UserRegisterNumberSchema, user_service: UserServiceDep):
    await user_service.create_user_with_verification(request, response, user)
    
    
@router.post('/verify_code')
async def verify_code(request: Request, response: Response, code: int, user_service: UserServiceDep):
    await user_service.confirm_and_register_user(request, response, code)


@router.post('/login_with_email')
async def login_with_email(response: Response, user: UserAuthEmailSchema, user_service: UserServiceDep):
    await user_service.auth_user(response, user)
    
    
@router.post('/login_with_number')
async def login_with_number(response: Response, user: UserAuthNumberSchema, user_service: UserServiceDep):
    await user_service.auth_user(response, user)
    
    
# дописать
@router.post('/change_email')
async def change_email(request: Request, response: Response, new_email: str, session = Depends(get_session)):
    users_service = UserService(session)
    user = await users_service.get_user_from_token(request, response)
    await users_service.change_email(new_email)
    
    
# дописать
@router.post('/change_number')
async def change_number(response: Response, new_number, session = Depends(get_session)):
    users_services = UserService(session)
    await users_services.change_number(new_number)

    
@router.post('/logout')
async def login(response: Response, user_service: UserServiceDep):
    user_service.logout_user(response)
    

@router.post('/delete_user')
async def delete_user(response: Response, user_service: UserServiceDep, user: CurrentUserDep):
    await user_service.delete_user(user, response)


@router.post('/test/')
async def test(user: CurrentUserDep):
    print(user.email)