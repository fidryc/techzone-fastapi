from datetime import datetime, timedelta, timezone
from json import dumps

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.email.email_template import register_code
from app.email.servises import send_email
from app.exceptions import HttpExc401Unauth, HttpExc409Conflict
from app.redis.client import redis_client
from app.redis.utils import redis_get_data, redis_rerecord_tries_with_ttl
from app.users.dao import RefreshTokenBLDao, UserDao
from app.users.jwt import (create_and_set_token_verif_email, create_token,
                           get_access_token, get_refresh_token,
                           get_verif_token, set_token, validate_exp_token,
                           validate_payload_fields)
from app.users.schema import UserAuthSchema, UserSchema
from app.users.utils import (check_pwd, get_hash, prepare_user_for_auth,
                             random_code, validate_tries, verif_code)


class UserService:
    exp_access_token = timedelta(seconds=settings.EXP_SEC).total_seconds()
    exp_refresh_token = timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds()
    
    def __init__(self, session):
        self.dao = UserDao(session)
    
    async def create_user_with_verification(self, response: Response, user):
        """
            Проверяет уникальность пользователя, выставляет токен, чтобы не передавать свои данные опять,
            сохраняет данные в redis вместе с верным кодом для завершения регистрации
            с помощью функции "confirm_email_and_register_user"
        """
        try:
            await self.dao.check_user(user.email, user.number)
            
            data = prepare_user_for_auth(user)
            await redis_client.set(f'verify_code_user:{user.email}', dumps(data), ex=settings.VER_CODE_EXP_SEC)
            
            create_and_set_token_verif_email(response, user)
            email_to='f98924746@gmail.com'
            msg = register_code(email_to, data['code'])
            await send_email(msg)
            
        except IntegrityError:
            raise HttpExc409Conflict('Email или номер уже используются')
    
    
    async def confirm_email_and_register_user(self, request: Request, code_from_user):
        """
            Получает email пользователя, который пытается зарегистрироваться, 
            достает все данные пользователя вместе с верным кодом.
            В случае верного переданного кода регистрирует его. 
            Если код неверный, то повышает счетчик попыток.
            Если попытки закончены, то будет выбрасываться исключение
        """
        
        payload = get_verif_token(request)
        key = f'verify_code_user:{payload['user_email']}'
        data = await redis_rerecord_tries_with_ttl(key)
        validate_tries(data['try'])
        verif_code(code_from_user, data['code'])
        await self.dao.add(**data['user'])
        return 'Пользователь успешно создан!'
        
    @staticmethod
    def logout_user(response: Response):
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
    async def get_user_from_token(self, request: Request, response: Response):
        """
            Получение user из токена, вместе с обновлением access при актуальности refresh token
        """
        try:
            token_payload = get_access_token(request)
            validate_payload_fields(token_payload)
        
            user_from_access_token = await self.dao.find_user(token_payload['user_email'], token_payload['user_number'])
            if not user_from_access_token:
                raise HttpExc401Unauth('Неверный email или number')
        
            validate_exp_token(token_payload)
            
            return user_from_access_token
        
        except HTTPException:
            print('Access token истек. Пытаемя сделать новый')
            refresh_token = get_refresh_token(request)
            validate_payload_fields(refresh_token)
            validate_exp_token(refresh_token)
            
            bl_token_dao = RefreshTokenBLDao(self.dao.session)
            bl_token = await bl_token_dao.get_reftoken_bl(refresh_token['jti'])
            if bl_token:
                self.logout_user(response)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Вы заблокированы')
            user_from_refresh_token = await self.dao.find_user(refresh_token['user_email'], refresh_token['user_number'])
            
            set_token(response, user_from_refresh_token, 'access')
    
            return user_from_refresh_token
    
    async def auth_user(self, response: Response, user: UserAuthSchema):
        user_in_db = await self.dao.find_user(user.email, user.number)
        print(user_in_db)
        if not user_in_db:
            raise HttpExc401Unauth('Неправильный номер телефона или почта')
        if not check_pwd(user.password, user_in_db.hashed_password):
            raise HttpExc401Unauth('Неправильный пароль')
        set_token(response, user_in_db, 'access')
        set_token(response, user_in_db, 'refresh')
        
        
