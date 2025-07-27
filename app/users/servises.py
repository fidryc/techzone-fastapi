from app.users.dao import UsersDao
from fastapi import HTTPException, Depends, Request, Response
from sqlalchemy.exc import IntegrityError
from app.email.servises import send_email
from app.email.email_template import register_code
from app.users.utils import get_hash
from app.users.jwt import get_access_token, get_refresh_token, set_token, validate_payload_fields, create_token, validate_exp_token
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
        
    async def get_user_from_token(self, request: Request, response: Response):
        token_payload = get_access_token(request)
        validate_payload_fields(token_payload)
        
        user = await self.dao.find_user(token_payload['user_email'], token_payload['user_number'])
        if not user:
            raise HTTPException(401, 'Неверный email или number')
        
        try:
            validate_exp_token(token_payload)
        
        except HTTPException:
            print('Access token истек. Пытаемя сделать новый')
            refresh_token = get_refresh_token(request)
            validate_exp_token(refresh_token)
            set_token(response, user, 'access')
    
        return user
    
    # СДЕЛАТЬ ЧЕРНЫЙ СПИСОК refresh
    
    async def auth_user(self, response: Response, user: UsersSchema):
        user_in_db = await self.dao.find_user(user.email, user.number)
        if not user_in_db:
            raise HTTPException(401, 'Неправильный номер телефона или почта')
        if not check_pwd(user.password, user_in_db.hashed_password):
            raise HTTPException(401, detail='Неправильный пароль')
        jwt = create_token(user, 'access')
        jwt_refresh = create_token(user, 'refresh')
        response.set_cookie('access_token', jwt)
        response.set_cookie('refresh_token', jwt_refresh, max_age=int(self.exp_refresh_token))
        
        
        