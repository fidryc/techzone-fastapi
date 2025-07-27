from app.users.dao import UsersDao
from fastapi import HTTPException, Depends, Request, Response
from sqlalchemy.exc import IntegrityError
from app.email.servises import send_email
from app.email.email_template import register_code
from app.users.utils import get_hash
from app.users.jwt import get_jwt, get_refresh_jwt, validate_payload, create_jwt
from datetime import datetime, timedelta, timezone
from app.users.schema import UsersSchema
from app.users.utils import check_pwd
from app.config import settings

class UsersServices:
    exp_access_token = timedelta(seconds=settings.EXP_SEC).total_seconds()
    exp_refresh_token = timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds()
    def __init__(self, session):
        self.dao = UsersDao(session)
    
    async def add_user(self, user):
        try:
            async with self.dao.session.begin():
                await self.dao.check_user(user.email, user.number)
                hashed_password = get_hash(user.password)
                await self.dao.add(email = user.email,
                        hashed_password = hashed_password,
                        city = user.city,
                        home_address = user.home_address,
                        pickup_store = user.pickup_store,
                        number = user.number)
            email_to='alexeylazarev2007@mail.ru'
            msg = register_code(email_to)
            await send_email(msg)
            
        except IntegrityError:
            raise HTTPException(status_code=422, detail='Email или номер уже используются')
        
    async def get_current_user(self, request: Request, response: Response):
        token_payload = get_jwt(request)
        
        validate_payload(token_payload)
        
        user_by_email = await self.dao.find_by_filter(email=token_payload['user_email'])
        user_by_email = user_by_email[0]
        
        if user_by_email.email != token_payload['user_email']:
            raise HTTPException(401, 'email либо не существует в базе либо email неправильный')
        
        exp = token_payload['exp']
        if datetime.now(timezone.utc).timestamp() > exp:
            print('ВРЕМЯ JWT ВЫШЛО, ПЫТАЕМСЯ СДЕЛАТЬ НОВЫЙ')
            access_refresh_token = get_refresh_jwt(request)
            exp_refresh = access_refresh_token['exp']
            if datetime.now(timezone.utc).timestamp() > exp_refresh:
                raise HTTPException(401, 'время токена вышло')
            jwt = create_jwt(user_by_email, timedelta(seconds=settings.EXP_SEC))
            response.set_cookie('access_token', jwt)
            print('СДЕЛАН НОВЫЙ ТОКЕН jwt')
        return user_by_email
        
    async def auth_user(self, response: Response, user: UsersSchema):
        user_in_db = await self.dao.find_user(user.email, user.number)
        user_in_db = user_in_db[0]
        if not user_in_db:
            raise HTTPException(401, 'Неправильный номер телефона или почта')
        if not check_pwd(user.password, user_in_db.hashed_password):
            raise HTTPException(401, detail='Неправильный пароль')
        jwt = create_jwt(user, timedelta(seconds=settings.EXP_SEC))
        jwt_refresh = create_jwt(user, timedelta(days=settings.EXP_REFRESH_DAYS))
        response.set_cookie('access_token', jwt)
        response.set_cookie('access_refresh_token', jwt_refresh, max_age=int(self.exp_refresh_token))
        
        
        