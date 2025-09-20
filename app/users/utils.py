import json
from random import randint

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException

from app.redis.client import redis_client

from app.config import settings
from app.users.schema import UserSchema


def get_hash(password: str) -> tuple[str, str]:
    """
    Хеширует пароль с солью и возвращает пароль и соль
    """
    salt = gensalt()
    password_bytes = password.encode('utf-8')
    hashed_password = hashpw(password_bytes, salt)
    
    return hashed_password.decode('utf-8')


def check_pwd(pwd: str, hash_pwd: str):
    pwd_bytes = pwd.encode('utf-8')
    hash_pwd = hash_pwd.encode('utf-8')
    return checkpw(pwd_bytes, hash_pwd)


def random_code():
    return randint(100000, 999999)


def verify_code(user_code, code):
        if int(user_code) != code:
            raise HTTPException(401, 'Неверный код')
        return True
    
    
def validate_tries(tries):
    if tries > settings.MAX_TRIES_EMAIL_CODE:
        raise HTTPException(401, 'Попробуйте ввести email еще раз')


def prepare_user_for_auth(user, code):
    hashed_password = get_hash(user.password)
            
    user_dict = {'email': user.email,
            'hashed_password': hashed_password,
            'city': user.city,
            'home_address': user.home_address,
            'number': user.number}
    data = {
        'user': user_dict,
        'code': code,
        'try': 0
    }
    
    return data


