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
from app.orders.dao import OrderDao
from app.redis.services import RedisService
from app.tasks.email_tasks import send_email_code
from app.users.dao import RefreshTokenBLDao, UserDao
from app.users.jwt import (
    set_verify_register_token,
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
    logout_user,
    prepare_user_for_auth,
    random_code,
    verify_code,
)
from app.logger import logger, create_msg_db_error

class RefreshTokenBLService:
    def __init__(self, session: AsyncSession, refresh_token_bl_dao: RefreshTokenBLDao):
        self.refresh_token_bl_dao = refresh_token_bl_dao
        
    async def processing_refresh_token(self, response: Response, refresh_token):
        """
        Проверяет входит ли refresh_token в список заблокированных токенов
        
        Проверяет есть ли rf_token в blacklist. Если да, 
        то выбрасывает исключение с удаляет token из cookie
        """
        
        try:
            bl_token = await self.refresh_token_bl_dao.get_refresh_token_bl(refresh_token['jti'])
            if bl_token:
                logout_user(response)
                logger.warning('Refresh token in blacklist', extra={'jti': refresh_token['jti']})
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Сессия заблокирована')
            logger.debug('Refresh token successfully processed', extra={'jti': refresh_token['jti']})
        except HTTPException:
            raise
        except Exception:
            logger.error('Unexpected error in processing_refresh_token', extra={'jti': refresh_token.get('jti')}, exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при проверке refresh token')

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
        Удаляет пользователя
        
        Удаляет пользователя вместе со всеми связанными с ним данными

        Args:
            user (User): строка модели Users
            response (Response): удаление из cookie jwt токенов
        """
        try:
            active_orders = await self.order_dao.get_active_user_orders(user.user_id)
            if active_orders:
                logger.info('Account deletion refused: User has active orders', extra={'user_id': user.user_id, 'active_orders_count': len(active_orders)})
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Пользователь имеет активные заказы')
            
            await self.order_dao.delete_all_user_orders(user.user_id)
            await self.user_dao.delete_user(user.user_id)
            logout_user(response)
            logger.debug(f'Logout user {user.user_id}')
            await self.session.commit()
            logger.info('User successfully deleted', extra={'user_id': user.user_id})
        except HTTPException:
            raise
        except Exception:
            logger.error('Failed to delete user', extra={'user_id': user.user_id}, exc_info=True)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail='Ошибка при удалении пользователя')

    async def get_user_from_token(self, request: Request, response: Response):
        """
        Получение user из токена
        
        Получение user из токена, вместе с обновлением access, при актуальности refresh token
        """
        try:
            token_payload = get_access_token(request)
            validate_payload_fields(token_payload)

            user_from_access_token = await self.user_dao.find_user(
                token_payload['user_email'], token_payload['user_number']
            )
            if not user_from_access_token:
                logger.warning('User not found from access token', extra={'email': token_payload.get('user_email'), 'number': token_payload.get('user_number')})
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверный email или number')

            validate_exp_token(token_payload)
            logger.debug('User retrieved from access token', extra={'user_id': user_from_access_token.user_id})
            return user_from_access_token

        except HTTPException as e:
            if e.status_code != status.HTTP_401_UNAUTHORIZED:
                raise
            
            logger.debug('Access token expired, trying refresh token')
            try:
                refresh_token = get_refresh_token(request)
                validate_payload_fields(refresh_token)
                validate_exp_token(refresh_token)

                await self.refresh_token_bl_service.processing_refresh_token(response, refresh_token)
                
                user_from_refresh_token = await self.user_dao.find_user(
                    refresh_token['user_email'], refresh_token['user_number']
                )
                if not user_from_refresh_token:
                    logger.warning('User not found from refresh token', extra={'email': refresh_token.get('user_email'), 'number': refresh_token.get('user_number')})
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не авторизован')
                
                set_token(response, user_from_refresh_token, 'access')
                logger.info('Access token refreshed', extra={'user_id': user_from_refresh_token.user_id})
                return user_from_refresh_token
            except HTTPException:
                raise
            except Exception:
                logger.error('Failed to refresh access token', exc_info=True)
                raise HTTPException(status_code=500, detail='Ошибка при обновлении токена')

    async def login_user(self, response: Response, user: UserAuthEmailSchema | UserAuthNumberSchema):
        """
        Вход в аккаунт
        
        Вход в аккаунт по почте или номеру телефона с проверкой корректности введенных данных
        """
        try:
            user_in_db = await self.user_dao.find_user(user.email, user.number)
            if not user_in_db:
                logger.warning('Login failed: User not found', extra={'email': user.email, 'number': user.number})
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неправильный номер телефона или почта")
            
            if not check_pwd(user.password, user_in_db.hashed_password):
                logger.warning('Login failed: Incorrect password', extra={'user_id': user_in_db.user_id})
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неправильный пароль")
            
            set_token(response, user_in_db, "access")
            set_token(response, user_in_db, "refresh")
            logger.info('User logged in successfully', extra={'user_id': user_in_db.user_id})
        except HTTPException:
            raise
        except Exception:
            logger.error('Unexpected error during login', extra={'email': user.email, 'number': user.number}, exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при авторизации')
        
    def logout_user(self, response: Response):
        try:
            logout_user(response)
            logger.debug('Logout user')
        except Exception as e:
            logger.warning('Failed logout', exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при выходе с аккаунт') from e

class NotificationService(ABC):
    """Абстрактный класс для сервиса отправки уведомлений"""
    
    @abstractmethod
    async def send_verification_code(self, code: str) -> None:
        pass
    
    @abstractmethod
    def get_user_identifier(self):
        """Получение индентификатора пользователя"""
        pass
    
    
class NotificationEmailService(NotificationService):
    
    def __init__(self, user: UserRegisterEmailSchema):
        self.user = user
        
    def get_user_identifier(self) -> str:
        return self.user.email
        
    def send_verification_code(self, code):
        """Отправка кода на почту"""
        try:
            recipient = self.get_user_identifier()
            # TODO: поменять хардкод email
            recipient = "f98924746@gmail.com"
            send_email_code.delay(recipient, code)
            logger.info('Verification code sent to email', extra={'recipient': self.user.email})
        except Exception:
            logger.error('Failed to send verification code to email', extra={'recipient': self.user.email}, exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при отправке кода на email')
        
class NotificationNumberService(NotificationService):
    def __init__(self, user: UserRegisterNumberSchema):
        self.user = user
    
    def get_user_identifier(self) -> str:
        return self.user.number

    def send_verification_code(self, code):
        """Отправка кода на номер телефона"""
        try:
            # TODO: Сделать отправку кода в будущем
            recipient = self.get_user_identifier()
            recipient = "f98924746@gmail.com"
            send_email_code.delay(recipient, code)
            logger.info('Verification code sent to number', extra={'recipient': self.user.number})
        except Exception:
            logger.error('Failed to send verification code to number', extra={'recipient': self.user.number}, exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при отправке кода на номер телефона')
        

class NotificationServiceFactory:
    def __init__(self, user: UserRegisterEmailSchema | UserRegisterNumberSchema):
        self.user = user
    
    def get_notification_service(self) -> NotificationService:
        """Получение сервиса отправки кода в зависимости от его типа user"""
        if isinstance(self.user, UserRegisterEmailSchema):
            logger.debug('Creating NotificationEmailService')
            return NotificationEmailService(self.user)
        elif isinstance(self.user, UserRegisterNumberSchema):
            logger.debug('Creating NotificationNumberService')
            return NotificationNumberService(self.user)
        else:
            logger.error('Unknown user type for notification service', extra={'user_type': type(self.user).__name__})
            raise ValueError('Неизвестный тип пользователя для отправки уведомлений')
        

class RegisterService:
    def __init__(self,
                 user_dao: UserDao,
                 redis_service: RedisService,
                 session: AsyncSession):
        self.user_dao = user_dao
        self.redis_service = redis_service
        self.session = session
    
    def _get_data_for_registration(self, user) -> UserAuthRedisSchema:
        """
        Получение данных для redis для дальнейшей регистрации.
        
        Получение данных для redis для дальнейшей регистрации.
        Включает в себя данные пользователя, код, попытку регистрации
        """
        try:
            code = random_code()
            data = prepare_user_for_auth(user, code)
            logger.debug('Registration data prepared', extra={'has_code': bool(code)})
            return data
        except Exception:
            logger.error('Failed to prepare registration data', exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при подготовке данных регистрации')
        
    async def initiate_registration(self, request: Request, response: Response, user: UserRegisterEmailSchema | UserRegisterNumberSchema, notification_service: NotificationService):
        """
        Инициализация регистрации пользователя
        
        Проверяет уникальность пользователя, выставляет токен, чтобы не передавать данные для регистрации опять,
        сохраняет данные в redis вместе с верным кодом для завершения регистрации с помощью функции confirm_email_and_register_user.
        Также не дает кидать большое количество кодов с одного ip.
        """
        
        try:
            await self.redis_service.processing_limit_ip(request.client.host)
            await self.user_dao.check_user(user.email, user.number)
            
            data = self._get_data_for_registration(user)
            user_identifier = notification_service.get_user_identifier()
            
            await self.redis_service.set_user_auth_data(user_identifier, data)
            set_verify_register_token(response, user_identifier)
            notification_service.send_verification_code(code=data['code'])
            # await notification_service.send_verification_code(data['code'])
            
            logger.info('Registration initiated', extra={'user_identifier': user_identifier, 'ip': request.client.host})
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to initiate registration', extra={'email': user.email, 'number': user.number, 'ip': request.client.host}, exc_info=True)
            raise HTTPException(status_code=500, detail='Ошибка при инициализации регистрации') from e
        
    async def confirm_and_register_user(
        self, request: Request, response: Response, code_from_user: str
    ):
        """
        Завершение регистрации с подверждением кода
        
        Получает email пользователя, который пытается зарегистрироваться,
        достает все данные пользователя вместе с верным кодом.
        В случае верного переданного кода регистрирует его.
        Если код неверный, то повышает счетчик попыток.
        Если попытки закончены, то будет выбрасываться исключение
        """
        
        verify_register_key = None
        try:
            payload = get_verify_token(request)
            verify_register_key = payload['verify_register_key']
            key = f'verify_code_user:{verify_register_key}'
            
            data = await self.redis_service.get_user_auth_data(key)
            if not data:
                logger.warning('Registration data not found in Redis', extra={'key': key})
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Данные регистрации не найдены. Попробуйте зарегистрироваться снова')
            
            if not self.redis_service.is_correct_attempt(data['attempt']):
                logger.warning('Registration attempts exceeded', extra={'verify_key': verify_register_key, 'attempts': data['attempt']})
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Попробуйте зарегистрироваться снова')
            
            try:
                verify_code(code_from_user, data["code"])
            except ValueError:
                logger.warning('Invalid verification code provided', extra={'verify_key': verify_register_key})
                # Увеличить счетчик попыток в Redis
                await self.redis_service.increment_attempt(key)
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Передан неверный код')
            
            await self.user_dao.add(**data["user"])
            await self.session.commit()
            logger.info('User successfully registered', extra={'verify_key': verify_register_key, 'email': data["user"].get("email"), 'number': data["user"].get("number")})
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Failed to confirm and register user', extra={'verify_key': verify_register_key}, exc_info=True)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail='Ошибка при завершении регистрации') from e
        finally:
            response.delete_cookie(settings.JWT_VERIFY_REGISTRATION_COOKIE_NAME)
            logger.debug('Verify register token cookie deleted')