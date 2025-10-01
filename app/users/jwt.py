from jwt import encode, decode
import cryptography
from app.config import settings
from app.users.schema import UserSchema
from datetime import datetime, timedelta, timezone
from fastapi import (Request, Response, HTTPException)
import uuid
from app.exceptions import HttpExc401Unauth


def set_verify_register_token(
    response: Response,
    key: str
):
    payload = {
            'verify_register_key': str(key),
        }
    verify_register_token = encode(payload, key=settings.PRIVATE_SECRET_KEY, algorithm=settings.ALGORITM)
    response.set_cookie('verify_register_token', verify_register_token)
    

def get_verify_token(request: Request):
    token = request.cookies.get('verify_register_token')
    if not token:
        raise HttpExc401Unauth('Не передан токен подтверждения регистрации.')
    try:
        token_payload: dict = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM, options={"verify_exp": False})
        if not token_payload.get('verify_register_key', None):
            raise HttpExc401Unauth('Неверный токен подтверждения.')
        return token_payload
    except:
        raise HttpExc401Unauth('Ошибка декодировки токена подверждения регистрации')
    
def create_token(user: UserSchema, type: str):
    jti = str(uuid.uuid4())
    if type == 'access':
        time_exp = datetime.now(timezone.utc) + timedelta(seconds=settings.EXP_SEC)
    elif type == 'refresh':
        time_exp = datetime.now(timezone.utc) + timedelta(days=settings.EXP_REFRESH_DAYS)
        
    payload = {
            'jti': jti,
            'user_email': str(user.email),
            'user_number': str(user.number),
            'user_role': str(user.role),
            'exp': time_exp.timestamp(),
            'type': str(type)
        }
    jwt = encode(payload, key=settings.PRIVATE_SECRET_KEY, algorithm=settings.ALGORITM)
    
    return jwt
    
def set_token(response: Response, user, type):
    if type == 'access':
        token = create_token(user, 'access')
        response.set_cookie('access_token', token, httponly=True)
    if type == 'refresh':
        token = create_token(user, 'refresh')
        response.set_cookie('refresh_token', token, httponly=True, max_age=int(timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds()))


def get_access_token(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HttpExc401Unauth('Нет токена для проверки аккаунт')
    try:
        payload = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM,  options={"verify_exp": False})
        if payload.get('type') != 'access':
            raise HttpExc401Unauth('Токен access подделан')
        return payload
    except:
        raise HttpExc401Unauth('Ошибка декодировки access токена')
    
def get_refresh_token(request: Request):
    token = request.cookies.get('refresh_token')
    if not token:
        raise HttpExc401Unauth('refresh token нет. Авторизуйтесь заново')
    try:
        payload: dict = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM,  options={"verify_exp": False})
        if payload.get('type') != 'refresh':
            raise HttpExc401Unauth('Токен refresh подделан')
        return payload
    except:
        raise HttpExc401Unauth('Ошибка декодировки refresh')
    
def validate_payload_fields(token_payload):
    """
        Проверка, что email или number существует и корректный
    """
    jti = token_payload.get('jti', None)
    if not jti or not isinstance(jti, str):
        raise ValueError('неправильное поле jti')
    user_email = token_payload.get('user_email', None)
    user_number = token_payload.get('user_number', None)
    if (not user_email and not user_number) or (not (isinstance(user_email, str)) and not (isinstance(user_number, str))):
        raise ValueError('неправильное поле user_email')
    user_role = token_payload.get('user_role', None)
    if not user_role or not isinstance(user_role, str):
        raise ValueError('неправильное поле user_role')
    exp = token_payload.get('exp', None)
    if not exp or not isinstance(exp, float):
        raise ValueError('неправильное поле exp')
    type = token_payload.get('type', None)
    if not type or type not in ('access', 'refresh'):
        raise ValueError('неправильное поле type')
    
def validate_exp_token(token):
    if datetime.now(timezone.utc).timestamp() > token['exp']:
        raise HttpExc401Unauth(f'Время токена истекло {token['type']}')
    return True

    

