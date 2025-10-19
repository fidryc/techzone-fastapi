from pydantic import BaseModel, EmailStr, field_validator, model_validator, Field
from re import fullmatch
from typing import Optional, TypedDict
import random


    
class UserSchema(BaseModel):
    user_id: int
    email: str
    hashed_password: str
    city: str
    home_address: str
    pickup_store_id: int
    number: str
    role: str
    
    
class UserValidateUtils:
    
    @classmethod
    def validate_email(email):
        if not fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+', email):
            raise ValueError('Введенный email неверный')
        return email
    
    
    @classmethod
    def convert_number(cls, number: str):
        """Перевод номера в формат +7XXXXXXXXXX"""
        number_for_bd = '+'
        for ch in number:
            if ch.isdigit():
                number_for_bd += ch
        if number_for_bd[1] == '8':
            number_for_bd = '+7' + number_for_bd[2:]
        return number_for_bd
    

    @classmethod
    def validate_number(cls, number):
        """
        Валидация русских номеров телефона
        
        Варианты:
            +7XXXXXXXXXX
            8XXXXXXXXXX
            +7 (XXX) XXX-XX-XX
            8 (XXX) XXX-XX-XX
            +7-XXX-XXX-XX-XX
            +7 XXX XXX XXXX
        """
        
        pattern = r'(\+7|8)[ -]?\d{3}[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}'
        if not fullmatch(pattern, number):
            raise ValueError('Неверный формат номера')
        return cls.convert_number(number)
    
    
class BaseUserRegisterSchema(BaseModel):
    password: str
    city: str
    home_address: None = None
    pickup_store: None = None
    
    @staticmethod
    def check_digits(password: str, need_count: int) -> bool:
        counter = 0
        for ch in password:
            if ch.isdigit():
                counter += 1
            if counter == need_count:
                return True
        else:
            return False
       
    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str):
        if len(password) >= 8 and cls.check_digits(password, 3):
            return password
        raise ValueError('Неверный пароль')
    

class UserRegisterEmailSchema(BaseUserRegisterSchema):
    email: str
    number: None = Field(default=None, exclude=True)
    
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, email):
        UserValidateUtils.validate_email(email)
    
    
    @field_validator('number')
    @classmethod
    def validate_email(cls, number):
        if number:
            raise ValueError('Нельзя передавать number при регистрации по email')
        return None
    
    @model_validator(mode='after')
    def validate_fields(self):
        if self.password == self.email.split('@')[0]:
            raise ValueError('Пароль должен быть отличен от email')
        return self
    
    
class UserRegisterNumberSchema(BaseUserRegisterSchema):
    email: None = Field(default=None, exclude=True)
    number: str = Field(example=f'+7{random.randint(int('1'*10), int('9'*10))}')
    
    
    @field_validator('number')
    @classmethod
    def validate_number(cls, number):
        correct_number = UserValidateUtils.convert_number(number)
        UserValidateUtils.validate_number(correct_number)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, email):
        if email:
            raise ValueError('Нельзя передавать email при регистрации по number')
        return None
    
    
class UserAuthBaseSchema(BaseModel):
    password: str
    
    
class UserAuthEmailSchema(UserAuthBaseSchema):
    email: str
    number: None = Field(default=None)


class UserAuthNumberSchema(UserAuthBaseSchema):
    number: str
    email: None = Field(default=None)
    

class UserAuthRedisSchema(TypedDict):
    user: dict
    code: int
    attempt: int