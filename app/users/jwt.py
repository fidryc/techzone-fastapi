from jwt import encode, decode
import cryptography
from app.config import settings
from app.users.schema import UsersSchema
from datetime import datetime, timedelta, timezone
from fastapi import (Request, Response, HTTPException)
import uuid

def create_token(
    user: UsersSchema,
    type: str,
):
    if type == 'access':
        time_exp = datetime.now(timezone.utc) + timedelta(seconds=settings.EXP_SEC)
    elif type == 'refresh':
        jti = str(uuid.uuid4())
        time_exp = datetime.now(timezone.utc) + timedelta(days=settings.EXP_REFRESH_DAYS)
        
    payload = {
            'jti': jti,
            'user_email': str(user.email),
            'user_number': str(user.number),
            'exp': time_exp.timestamp(),
            'type': type
        }
    jwt = encode(payload, key=settings.PRIVATE_SECRET_KEY, algorithm=settings.ALGORITM)
    
    return jwt
    
def set_token(response: Response, user: UsersSchema, type):
    if type == 'access':
        token = create_token(user, 'access')
        response.set_cookie('access_token', token, httponly=True)
    if type == 'refresh':
        token = create_token(user, 'refresh')
        response.set_cookie('refresh_token', token, httponly=True, max_age=int(timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds()))


def get_access_token(request: Request):
    token = request.cookies.get('access_token')
    if not token or token['type'] == 'access':
        raise HTTPException(401, 'Не авторизован jwt')
    try:
        payload = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM,  options={"verify_exp": False})
        return payload
    except:
        raise HTTPException(401, 'jwt')
    
def get_refresh_token(request: Request):
    token = request.cookies.get('refresh_token')
    if not token and token['type'] == 'refresh':
        raise HTTPException(401, 'refresh token нет. Авторизуйтесь заново')
    try:
        payload = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM,  options={"verify_exp": False})
        return payload
    except:
        raise HTTPException(401, 'refresh')
    
def validate_payload_fields(token_payload):
    """
        Проверка, что email или number существует и корректный
    """
    
    user_email = token_payload.get('user_email', None)
    user_number = token_payload.get('user_number', None)
    if (not user_email and not user_number) or (not (isinstance(user_email, str)) and not (isinstance(user_number, str))):
        raise ValueError('неправильное поле user_email')
    exp = token_payload.get('exp', None)
    if not exp or not isinstance(exp, float):
        raise ValueError('неправильное поле exp')
    type = token_payload.get('type', None)
    if not type or type not in ('access', 'refresh'):
        raise ValueError('неправильное поле type')
    
def validate_exp_token(token):
    if datetime.now(timezone.utc).timestamp() > token['exp']:
        raise HTTPException(401, f'Время токена истекло {token['type']}')
    return True

def tdt_token(type):
    timedt = {
        'access': timedelta(seconds=settings.EXP_SEC),
        'refresh': timedelta(days=settings.EXP_REFRESH_DAYS)
    }
    return timedt[type]
    

