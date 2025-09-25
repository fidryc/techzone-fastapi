from datetime import datetime, timedelta, timezone
from json import dumps
from typing import Union

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.email.email_template import register_code
from app.email.servises import async_send_email
from app.exceptions import HttpExc401Unauth, HttpExc409Conflict
from app.orders.dao import OrderDao
from app.redis.services import RedisService
from app.redis.utils import redis_delete, redis_get_data, redis_record_tries_with_ttl
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
    UserRegisterEmailSchema,
    UserRegisterNumberSchema,
    UserSchema,
)
from app.users.utils import (
    check_pwd,
    get_hash,
    prepare_user_for_auth,
    random_code,
    valid_attempt,
    verify_code,
)


class RegisterService:
    
    def __init__(self, user: UserRegisterEmailSchema | UserRegisterNumberSchema):
        self.user = user


    def get_user_identifier(self):
        """Получаем значение, которое будет вставлено в редис по ключу для подтверждения регистрации"""
        
        if self.user.email:
            return self.user.email
        else:
            return self.user.number


    @staticmethod
    async def _send_email_code(recipient, code):
        recipient = "f98924746@gmail.com"
        msg = register_code(recipient, code)
        await async_send_email(msg)


    @staticmethod
    async def _send_number_code(recipient, code):
        # доработать, может сделать мок функцию
        recipient = "f98924746@gmail.com"
        msg = register_code(recipient, code)
        await async_send_email(msg)

    def _choose_send_code_method(self):
        if self.user.email:
            return self._send_email_code
        else:
            return self._send_number_code

    async def send_code(self, recipient, code):
        send_code_method = self._choose_send_code_method()
        await send_code_method(recipient, code)

    def set_verify_register_token(self, response):
        """
        Получаем user_identifier для ключа для редиса и в jwt токене ставим это значение,
        так как по нему будет вестись поиск, после обработки токена
        """
        user_identifier = self.get_user_identifier()
        set_verify_register_token(response, user_identifier)


class UserService:
    exp_access_token = int(timedelta(seconds=settings.EXP_SEC).total_seconds())
    exp_refresh_token = int(timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds())

    def __init__(self, user_dao: UserDao, order_dao: OrderDao, redis_service: RedisService, session: AsyncSession):
        self.session = session
        self.user_dao = user_dao
        self.order_dao = order_dao
        self.redis_service = redis_service

    async def create_user_with_verification(self, request: Request, response: Response, user: UserRegisterEmailSchema | UserRegisterNumberSchema):
        """
        Проверяет уникальность пользователя, выставляет токен, чтобы не передавать свои данные опять,
        сохраняет данные в redis вместе с верным кодом для завершения регистрации
        с помощью функции "confirm_email_and_register_user"
        """
        
        register_service = RegisterService(user)
        await self.redis_service.validate_ip_limit(request.client.host)
        await self.redis_service.set_limit_for_ip(request.client.host)
        await self.user_dao.check_user(user.email, user.number)
        code = random_code()
        data = prepare_user_for_auth(user, code)
        user_identifier = register_service.get_user_identifier()
        await self.redis_service.set_user_auth_data(user_identifier, data)
        set_verify_register_token(response, user_identifier)
        await register_service.send_code(user_identifier, code)

    async def confirm_and_register_user(
        self, request: Request, response: Response, code_from_user
    ):
        """
        Получает email пользователя, который пытается зарегистрироваться,
        достает все данные пользователя вместе с верным кодом.
        В случае верного переданного кода регистрирует его.
        Если код неверный, то повышает счетчик попыток.
        Если попытки закончены, то будет выбрасываться исключение
        """

        payload = get_verify_token(request)
        key = f"verify_code_user:{payload['verify_register_key']}"
        data = await redis_record_tries_with_ttl(key)
        if not valid_attempt(data["attempt"]):
            await redis_delete(key)
            raise HttpExc401Unauth('Количество попыток вышло. Попробуйте зарегестрироваться ещ раз')
        if not verify_code(code_from_user, data["code"]):
            raise HttpExc409Conflict('Передан неверный код')
        await self.user_dao.add(**data["user"])

        await self.session.commit()
        response.delete_cookie("verify_register_token")
        return "Пользователь успешно создан!"

    async def delete_user(self, user, response):
        """

        Удаляет пользователя вместе с заказами, проверив все ли заказы завершены.
        Автоматически удаляются детали заказов из order_details таблиц

        Args:
            user (User): строка модели Users
            response (Response): удаление из cookie jwt токенов
        """
        active_orders = await self.order_dao.get_active_user_orders(user.user_id)
        if active_orders:
            raise HttpExc409Conflict(
                "Вы не можете удалить аккаунт, так как у вас есть активыне заказы"
            )

        await self.order_dao.delete_all_user_orders(user.user_id)
        await self.user_dao.delete_user(user.user_id)
        self.logout_user(response)

        await self.session.commit()

    @staticmethod
    def logout_user(response: Response):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

    async def get_user_from_token(self, request: Request, response: Response):
        """
        Получение user из токена, вместе с обновлением access при актуальности refresh token
        """
        try:
            token_payload = get_access_token(request)
            validate_payload_fields(token_payload)

            user_from_access_token = await self.user_dao.find_user(
                token_payload["user_email"], token_payload["user_number"]
            )
            if not user_from_access_token:
                raise HttpExc401Unauth("Неверный email или number")

            validate_exp_token(token_payload)

            return user_from_access_token

        except HTTPException:
            print("Access token истек. Пытаемcя сделать новый")
            refresh_token = get_refresh_token(request)
            validate_payload_fields(refresh_token)
            validate_exp_token(refresh_token)

            bl_token_dao = RefreshTokenBLDao(self.user_dao.session)
            bl_token = await bl_token_dao.get_reftoken_bl(refresh_token["jti"])
            if bl_token:
                self.logout_user(response)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Вы заблокированы"
                )
            user_from_refresh_token = await self.user_dao.find_user(
                refresh_token["user_email"], refresh_token["user_number"]
            )

            set_token(response, user_from_refresh_token, "access")

            return user_from_refresh_token


    async def auth_user(self, response: Response, user: UserAuthEmailSchema | UserAuthNumberSchema):
        user_in_db = await self.user_dao.find_user(user.email, user.number)
        if not user_in_db:
            raise HttpExc401Unauth("Неправильный номер телефона или почта")
        if not check_pwd(user.password, user_in_db.hashed_password):
            raise HttpExc401Unauth("Неправильный пароль")
        set_token(response, user_in_db, "access")
        set_token(response, user_in_db, "refresh")

