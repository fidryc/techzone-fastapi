from datetime import datetime, timedelta
from fastapi import APIRouter, Path
from app.email.email_template import register_code
from app.email.servises import send_email
from app.redis.depends import RedisServiceDep
from app.users.depends import CurrentUserDep, RegisterServiceDep, UserDaoDep, UserServiceDep
from app.users.schema import UserAuthEmailSchema, UserAuthNumberSchema, UserRegisterEmailSchema, UserRegisterNumberSchema, UserSchema
from app.users.services import NotificationServiceFactory, RegisterService, UserService
from fastapi import Depends, Response, Request
from app.database import SessionDep, get_session

router = APIRouter(
    prefix='/users',
    tags=['Пользователь']
)
    
    
@router.post('/register_with_email')
async def register_with_email(request: Request, response: Response, user: UserRegisterEmailSchema, redis_service: RedisServiceDep, user_dao: UserDaoDep, session: SessionDep):
    notification_service = NotificationServiceFactory(user).get_notification_service()
    register_service = RegisterService(user_dao, redis_service, session)
    await register_service.initiate_registration(request, response, user, notification_service)
    
    
@router.post('/register_with_number')
async def register_with_number(request: Request, response: Response, user: UserRegisterNumberSchema, redis_service: RedisServiceDep, user_dao: UserDaoDep, session: SessionDep):
    notification_service = NotificationServiceFactory(user).get_notification_service()
    register_service = RegisterService(user_dao, redis_service, session)
    await register_service.initiate_registration(request, response, user, notification_service)
    
    
@router.post('/verify_code')
async def verify_code(request: Request, response: Response, confirm_code: int, register_service: RegisterServiceDep):
    await register_service.confirm_and_register_user(request, response, confirm_code)


@router.post('/login_with_email')
async def login_with_email(response: Response, user: UserAuthEmailSchema, user_service: UserServiceDep):
    await user_service.login_user(response, user)
    
    
@router.post('/login_with_number')
async def login_with_number(response: Response, user: UserAuthNumberSchema, user_service: UserServiceDep):
    await user_service.login_user(response, user)
    
    
# # дописать
# @router.post('/change_email')
# async def change_email(user: CurrentUserDep, user_service: UserServiceDep, new_email):
#     await user_service.change_email(user, new_email)
    
    
# # дописать
# @router.post('/change_number')
# async def change_number(response: Response, new_number, session = Depends(get_session)):
#     users_services = UserService(session)
#     await users_services.change_number(new_number)

    
@router.post('/logout')
async def login(response: Response, user_service: UserServiceDep):
    user_service.logout_user(response)
    

@router.post('/delete_user')
async def delete_user(response: Response, user_service: UserServiceDep, user: CurrentUserDep):
    await user_service.delete_user(user, response)


@router.post('/test/')
async def test(user: CurrentUserDep):
    print(user.email)