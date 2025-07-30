from pydantic import BaseModel, EmailStr, field_validator, model_validator, Field
from re import fullmatch
from typing import Optional
import random

class UsersSchema(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = Field(None, example='t@gmail.com')
    password: str
    city: str
    home_address: str
    pickup_store: str
    number: Optional[str] = Field(None, example=f'+7{random.randint(int('1'*10), int('9'*10))}')

    
    @staticmethod
    def convert_number(number: str):
        """
        Перевод номера в формат +7XXXXXXXXXX
        """
        number_for_bd = '+'
        for ch in number:
            if ch.isdigit():
                number_for_bd += ch
        if number_for_bd[1] == '8':
            number_for_bd = '+7' + number_for_bd[2:]
        return number_for_bd
    
    @field_validator('number')
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
    
    @field_validator('email')
    def validate_email(cls, email):
        ru = 'mail|bk|list|inbox|yandex|ya|rambler|hotmail|outlook'
        en = 'gmail|yahoo|outlook|hotmail|aol|icloud|me|msn'
        if not any(
            [fullmatch(rf'[a-zA-ZА-Яа-я]+@({ru}).ru', email),
            fullmatch(rf'[a-zA-ZА-Яа-я]+@({en}).com', email)]
            ):
            raise ValueError('Введенный email неверный')
        return email
        
    
    @model_validator(mode='after')
    def validate_model(self):
        if not self.email and not self.number:
            raise ValueError('Должен быть указан хотя бы email или number')
        return self
    
class UsersAuthSchema(BaseModel):
    email: Optional[str] = Field(None)
    password: str
    number: Optional[str] = Field(None)
    
    