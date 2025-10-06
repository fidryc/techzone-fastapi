from random import randint

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, Response
from pydantic import BaseModel

from app.redis.client import redis_client

from app.config import settings
from app.users.schema import UserAuthRedisSchema, UserRegisterEmailSchema, UserRegisterNumberSchema


def get_hash(password: str) -> str:
    """Получение захешированного пароля с солью"""
    salt = gensalt()
    password_bytes = password.encode('utf-8')
    hashed_password = hashpw(password_bytes, salt)
    
    return hashed_password.decode('utf-8')


def check_pwd(pwd: str, hash_pwd: str) -> bool:
    """Проверка совпадения паролей"""
    pwd_bytes = pwd.encode('utf-8')
    hash_pwd_bytes = hash_pwd.encode('utf-8')
    return checkpw(pwd_bytes, hash_pwd_bytes)


def random_code() -> int:
    """Создает рандомный 6 значный код"""
    return randint(100000, 999999)


def verify_code(user_code: str, correct_code: int) -> bool:
    """Проверяет совпадение кодов"""
    try:
        return int(user_code) == correct_code
    except ValueError:
        return False
    
def logout_user(response: Response):
    """Удаляет из cookie все токены для аутенфикации пользователя"""
    response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME)
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME)
    
    
def prepare_user_for_auth(user: UserRegisterEmailSchema | UserRegisterNumberSchema, code: int) -> UserAuthRedisSchema:
    """Создает словарь, чтобы поместить в redis для дальнейшей регистрации"""
    
    user_dict = {'email': user.email,
            'number': user.number,
            'hashed_password': get_hash(user.password),
            'city': user.city,
            'number': user.number}
    data = {
        'user': user_dict,
        'code': code,
        'attempt': 0
    }
    return data


