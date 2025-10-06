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
    
    
@router.post(
        path='/register_with_email',
        summary='Инициализация регистрации по почте',
             )
async def register_with_email(
    request: Request,
    response: Response,
    user: UserRegisterEmailSchema,
    redis_service: RedisServiceDep,
    user_dao: UserDaoDep,
    session: SessionDep):
    """
    Инициализация регистрации по почте
    
    Генерирует код подверждения, сохраняет данные временно, возвращает jwt токен пользователю
    
    Args:
        user: данные пользователя для регистрации по почте
        
    Returns:
        200: токен сохранен в cookie
    """
    
    notification_service = NotificationServiceFactory(user).get_notification_service()
    register_service = RegisterService(user_dao, redis_service, session)
    await register_service.initiate_registration(request, response, user, notification_service)
    
    
@router.post(
    path='/register_with_number',
    summary='Инициализация регистрации по номеру телефона'
            )
async def register_with_number(request: Request, response: Response, user: UserRegisterNumberSchema, redis_service: RedisServiceDep, user_dao: UserDaoDep, session: SessionDep):
    """
    Инициализация регистрации по номеру телефона
    
    Генерирует код подверждения, сохраняет данные временно, возвращает jwt токен пользователю
    
    Args:
        user: данные пользователя для регистрации по номеру телефона
        
    Returns:
        200: токен сохранен в cookie
    """
    
    notification_service = NotificationServiceFactory(user).get_notification_service()
    register_service = RegisterService(user_dao, redis_service, session)
    await register_service.initiate_registration(request, response, user, notification_service)
    
    
@router.post(path='/verify_code',
             summary='Подверждение кода, чтобы успешно зарегестрироваться')
async def verify_code(request: Request, response: Response, confirm_code: int, register_service: RegisterServiceDep):
    """
    Подтверждения кода для регистрации
    
    Проверяет совпадение кодов, если совпали заносит ранее переданные данные в базу данных
    
    Args:
        confirm_code: код подверждения
    
    Returns:
        200: Пользователь успешно создан
    """
    
    await register_service.confirm_and_register_user(request, response, confirm_code)


@router.post(
    path='/login_with_email',
    summary='Вхождение в аккаунт по почте',
    )
async def login_with_email(response: Response, user: UserAuthEmailSchema, user_service: UserServiceDep):
    """
    Вход в аккаунт по email
    
    Вход в аккаунт с проверкой корректности переданных данных
    
    Args:
        user: данные пользователя
    
    Returns:
        200: Access jwt и refresh jwt успешно сохранены в cookie
    """
    
    await user_service.login_user(response, user)
    
    
@router.post(
    path='/login_with_number',
    summary='Вхождение в аккаунт по номеру телефона',
    )
async def login_with_number(response: Response, user: UserAuthNumberSchema, user_service: UserServiceDep):
    """
    Вход в аккаунт по номеру телефона
    
    Вход в аккаунт с проверкой корректности переданных данных
    
    Args:
        user: данные пользователя
    
    Returns:
        200: Access jwt и refresh jwt успешно сохранены в cookie
    """
    
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

    
@router.post(
    path='/logout',
    summary='Выход с аккаунта'
    )
async def login(response: Response, user_service: UserServiceDep):
    """
    Выход из аккаунта
    
    Завершает текущую сессию пользователя, удаляет токены авторизации
    
    Returns:
        200: Успешный выход из системы
    """
    
    user_service.logout_user(response)
    

@router.post(
    path='/delete_user',
    summary='Удаление аккаунта'
             )
async def delete_user(response: Response, user: CurrentUserDep, user_service: UserServiceDep):
    """
    Удаление аккаунта пользователя
    
    Полностью удаляет аккаунт пользователя и все связанные данные
    
    Args:
        user: текущий пользователь
    
    Returns:
        200: Аккаунт успешно удален
    """
    
    await user_service.delete_user(user, response)


@router.post(path='/test/',
             summary='Проверка правильности получения пользователя')
async def test(user: CurrentUserDep):
    """
    Тестовый эндпоинт
    
    Используется для тестирования функциональности аутентификации
    
    Args:
        user: текущий пользователь
    
    Returns:
        200: Тестовый ответ
    """
    
    return (user.email)