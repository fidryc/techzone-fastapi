from typing import TypedDict
import json
from random import randint
from re import fullmatch

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException
from pydantic import BaseModel

from app.redis.client import redis_client

from app.config import settings
from app.users.schema import UserRegisterEmailSchema, UserRegisterNumberSchema


def get_hash(password: str) -> str:
    salt = gensalt()
    password_bytes = password.encode('utf-8')
    hashed_password = hashpw(password_bytes, salt)
    
    return hashed_password.decode('utf-8')


def check_pwd(pwd: str, hash_pwd: str) -> bool:
    pwd_bytes = pwd.encode('utf-8')
    hash_pwd_bytes = hash_pwd.encode('utf-8')
    return checkpw(pwd_bytes, hash_pwd_bytes)


def random_code() -> int:
    return randint(100000, 999999)


def verify_code(user_code: str, correct_code: int) -> bool:
    try:
        return int(user_code) == correct_code
    except ValueError:
        return False
    
    
def valid_attempt(attempt: int) -> bool:
    return attempt < settings.MAX_TRIES_EMAIL_CODE


class UserAuthRedisSchema(TypedDict):
    user: dict
    code: int
    attempt: int
    
    
def prepare_user_for_auth(user: UserRegisterEmailSchema | UserRegisterNumberSchema, code: int) -> UserAuthRedisSchema:
    '''Создает словарь, чтобы поместить в redis для дальнейшей регистрации'''
    
    user_dict = {'email': user.email,
            'hashed_password': get_hash(user.password),
            'city': user.city,
            'number': user.number}
    data = {
        'user': user_dict,
        'code': code,
        'attempt': 0
    }
    return data


