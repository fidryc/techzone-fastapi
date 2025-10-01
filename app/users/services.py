from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from json import dumps
from typing import Union

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.email.email_template import register_code
from app.email.servises import async_send_email
from app.exceptions import DataBaseException, HttpExc401Unauth, HttpExc409Conflict, RefreshTokenBLServiceException
from app.orders.dao import OrderDao
from app.redis.services import RedisService
from app.users.dao import RefreshTokenBLDao, UserDao
from app.users.jwt import (
    set_verify_register_token,
    create_token,
    get_access_token,
    get_refresh_token,
    get_verify_token,
    set_token,
    validate_exp_token,
    validate_payload_fields,
)
from app.users.schema import (
    UserAuthEmailSchema,
    UserAuthNumberSchema,
    UserAuthRedisSchema,
    UserRegisterEmailSchema,
    UserRegisterNumberSchema,
    UserSchema,
)
from app.users.utils import (
    check_pwd,
    get_hash,
    logout_user,
    prepare_user_for_auth,
    random_code,
    verify_code,
)
from app.logger import logger

class RefreshTokenBLService:
    def __init__(self, session: AsyncSession, refresh_token_bl_dao: RefreshTokenBLDao):
        self.refresh_token_bl_dao = refresh_token_bl_dao
        
    async def processing_refresh_token(self, response: Response, refresh_token):
        '''Проверяет входит ли refresh_token в список заблокированных токенов'''
        bl_token = await self.refresh_token_bl_dao.get_refresh_token_bl(refresh_token['jti'])
        if bl_token:
            logout_user(response)
            logger.info('Refresh token in blacklist', extra={'bl_token': bl_token})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Сессия заблокирована')
        logger.info('Refresh token successfully processed', extra={'token': refresh_token})

class UserService:
    exp_access_token = int(timedelta(seconds=settings.EXP_SEC).total_seconds())
    exp_refresh_token = int(timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds())

    def __init__(
                 self,
                 user_dao: UserDao,
                 order_dao: OrderDao,
                 refresh_token_bl_service: RefreshTokenBLService,
                 redis_service: RedisService, 
                 session: AsyncSession
                 ):
        self.session = session
        self.user_dao = user_dao
        self.order_dao = order_dao
        self.refresh_token_bl_service = refresh_token_bl_service
        self.redis_service = redis_service

    async def delete_user(self, user: UserSchema, response: Response):
        """

        Удаляет пользователя вместе с заказами, проверив все ли заказы завершены.
        Автоматически удаляются детали заказов из order_details таблиц

        Args:
            user (User): строка модели Users
            response (Response): удаление из cookie jwt токенов
        """
        
        active_orders = await self.order_dao.get_active_user_orders(user.user_id)
        if active_orders:
            logger.info('Account deletion refusal:User has orders', extra={'user_id': user.user_id, 'orders': active_orders})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Пользователь имеет активные заказы')
        await self.order_dao.delete_all_user_orders(user.user_id)
        await self.user_dao.delete_user(user.user_id)
        logout_user(response)
        await self.session.commit()

    async def get_user_from_token(self, request: Request, response: Response):
        '''
        Получение user из токена, вместе с обновлением access, при актуальности refresh token
        '''
        try:
            token_payload = get_access_token(request)
            validate_payload_fields(token_payload)

            user_from_access_token = await self.user_dao.find_user(
                token_payload['user_email'], token_payload['user_number']
            )
            if not user_from_access_token:
                raise HttpExc401Unauth('Неверный email или number')

            validate_exp_token(token_payload)

            return user_from_access_token

        except HTTPException:
            logger.debug('Jwt access token expire', extra={'request': request, 'response': response})
            refresh_token = get_refresh_token(request)
            validate_payload_fields(refresh_token)
            validate_exp_token(refresh_token)

            await self.refresh_token_bl_service.processing_refresh_token(response, refresh_token)
            user_from_refresh_token = await self.user_dao.find_user(
                refresh_token['user_email'], refresh_token['user_number']
            )
            if not user_from_refresh_token:
                raise HttpExc401Unauth('Не авторизован')
            set_token(response, user_from_refresh_token, 'access')

            return user_from_refresh_token

    async def login_user(self, response: Response, user: UserAuthEmailSchema | UserAuthNumberSchema):
        user_in_db = await self.user_dao.find_user(user.email, user.number)
        if not user_in_db:
            raise HttpExc401Unauth("Неправильный номер телефона или почта")
        if not check_pwd(user.password, user_in_db.hashed_password):
            raise HttpExc401Unauth("Неправильный пароль")
        set_token(response, user_in_db, "access")
        set_token(response, user_in_db, "refresh")


class NotificationService(ABC):
    """Абстрактный класс для отправки уведомлений"""
    
    @abstractmethod
    async def send_verification_code(self, code: str) -> None:
        pass
    
    @abstractmethod
    def get_user_identifier(self):
        '''Получение либо number либо email'''
        pass
    
    
class NotificationEmailService(NotificationService):
    
    def __init__(self, user: UserRegisterEmailSchema):
        self.user = user
        
    def get_user_identifier(self) -> str:
        return self.user.email
        
    async def send_verification_code(self, code):
        '''Отправка кода на почту'''
        # поменять хардкод email
    
        recipient = self.get_user_identifier()
        recipient = "f98924746@gmail.com"
        msg = register_code(recipient, code)
        await async_send_email(msg)
        
class NotificationNumberService:
    def __init__(self, user: UserRegisterNumberSchema):
        self.user = user
    
    def get_user_identifier(self) -> str:
        return self.user.number

    async def send_verification_code(self, code):
        '''Отправка кода на номер телефона'''
        # Сделать отправку кода в будущем
        
        recipient = self.get_user_identifier()
        recipient = "f98924746@gmail.com"
        msg = register_code(recipient, code)
        await async_send_email(msg)
        
        
class NotificationServiceFactory:
    def __init__(self, user: UserRegisterEmailSchema | UserRegisterNumberSchema):
        self.user = user
    
    def get_notification_service(self) -> NotificationService:
        if isinstance(self.user, UserRegisterEmailSchema):
            return NotificationEmailService(self.user)
        elif isinstance(self.user, UserRegisterNumberSchema):
            return NotificationNumberService(self.user)
        

class RegisterService:
    def __init__(self,
                 user_dao: UserDao,
                 redis_service: RedisService,
                 session: AsyncSession):
        self.user_dao = user_dao
        self.redis_service = redis_service
        self.session = session
    
    def _get_data_for_registration(self, user) -> UserAuthRedisSchema:
        '''Получение данных для redis для дальнейшей регистрации. Включает в себя данные пользователя, код, попытку регистрации'''
        code = random_code()
        data = prepare_user_for_auth(user, code)
        return data
        
    async def initiate_registration(self, request: Request, response: Response, user: UserRegisterEmailSchema | UserRegisterNumberSchema, notification_service: NotificationService):
        """
        Проверяет уникальность пользователя, выставляет токен, чтобы не передавать свои данные опять,
        сохраняет данные в redis вместе с верным кодом для завершения регистрации
        с помощью функции "confirm_email_and_register_user"
        """
        await self.redis_service.processing_limit_ip(request.client.host)
        await self.user_dao.check_user(user.email, user.number)
        data = self._get_data_for_registration(user)
        user_identifier = notification_service.get_user_identifier()
        await self.redis_service.set_user_auth_data(user_identifier, data)
        set_verify_register_token(response, user_identifier)
        await notification_service.send_verification_code(data['code'])
        
    async def confirm_and_register_user(
        self, request: Request, response: Response, code_from_user: str
    ):
        '''
        Получает email пользователя, который пытается зарегистрироваться,
        достает все данные пользователя вместе с верным кодом.
        В случае верного переданного кода регистрирует его.
        Если код неверный, то повышает счетчик попыток.
        Если попытки закончены, то будет выбрасываться исключение
        '''
        try:
            payload = get_verify_token(request)
            key = f"verify_code_user:{payload['verify_register_key']}"
            data = await self.redis_service.get_user_auth_data(key)
            if not self.redis_service.is_correct_attempt(data['attempt']):
                raise HttpExc401Unauth('Попробуйте зарегистрироваться снова')
            try:
                verify_code(code_from_user, data["code"])
            except ValueError as e:
                raise HttpExc409Conflict('Передан неверный код')
            await self.user_dao.add(**data["user"])
            await self.session.commit()
        finally:
            response.delete_cookie('verify_register_token')
            