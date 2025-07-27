from jwt import encode, decode
import cryptography
from app.config import settings
from app.users.schema import UsersSchema
from datetime import datetime, timedelta, timezone
from fastapi import (Request, Response, HTTPException)


def create_jwt(
    user: UsersSchema,
    timedt: timedelta
):
    time_exp = datetime.now(timezone.utc) + timedt
    payload = {
        'user_email': str(user.email),
        'exp': time_exp.timestamp()
    }
    jwt = encode(payload, key=settings.PRIVATE_SECRET_KEY, algorithm=settings.ALGORITM)
    return jwt
    
def set_jwt(response: Response, user: UsersSchema):
    token = create_jwt(user)
    response.set_cookie('access_token', token)


def get_jwt(request: Request):
    token = request.cookies.get('access_token')
    print(token)
    if not token:
        raise HTTPException(401, 'Не авторизован jwt')
    try:
        payload = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM,  options={"verify_exp": False})
        return payload
    except:
        raise HTTPException(401, 'jwt')
    
def get_refresh_jwt(request: Request):
    token = request.cookies.get('access_refresh_token')
    if not token:
        raise HTTPException(401, 'Не авторизован refresh')
    try:
        payload = decode(token, settings.PUBLIC_SECRET_KEY, settings.ALGORITM,  options={"verify_exp": False})
        return payload
    except:
        raise HTTPException(401, 'refresh')
    
def validate_payload(token_payload):
    user_email = token_payload.get('user_email', None)
    if not user_email or not isinstance(user_email, str):
        raise ValueError('неправильное поле user_email')
    exp = token_payload.get('exp', None)
    if not exp or not isinstance(exp, float):
        raise ValueError('неправильное поле exp')

    

