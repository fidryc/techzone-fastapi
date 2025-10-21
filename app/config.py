from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, FilePath
from pathlib import Path
from dotenv import load_dotenv



class Settings(BaseSettings):
    MODE: Literal['DEV', 'TEST', 'PROD']
    LOG_LEVEL: Literal['INFO', 'DEBUG', 'WARNING', 'ERROR']

    DB_HOST: str
    DB_HOST_PROD: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    
    PRIVATE_SECRET_PATH: FilePath
    PUBLIC_SECRET_PATH: FilePath
    
    ALGORITM: str
    EXP_SEC: int
    EXP_REFRESH_DAYS: int
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    
    REDIS_HOST: str
    REDIS_HOST_PROD: str
    REDIS_PORT: int
    
    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    
    RBMQ_QUEUE_SEND_MAIL_ORDER_FORMATION: str

    VER_CODE_EXP_SEC: int
    
    MAX_TRIES_EMAIL_CODE: int
    
    ELASTIC_HOST: str
    ELASTIC_HOST_PROD: str
    ELASTIC_PORT: int
    
    INDEX_PRODUCTS: str
    
    LIMIT_SECONDS_GET_CODE: int
    
    JWT_ACCESS_COOKIE_NAME: str
    JWT_REFRESH_COOKIE_NAME: str
    JWT_VERIFY_REGISTRATION_COOKIE_NAME: str
    
    COURIER_EMAIL: str
    
    ADMIN_URL_STARTSWITH: str
    
    model_config = ConfigDict(env_file='.env')
        
    _private_secret_key_cache: str | None = None
    _public_secret_key_cache: str | None = None
        
    @property
    def PRIVATE_SECRET_KEY(self) -> str:
        if not self._private_secret_key_cache :
            self._private_secret_key_cache = Path(self.PRIVATE_SECRET_PATH).read_text()
        return self._private_secret_key_cache

    @property
    def PUBLIC_SECRET_KEY(self) -> str:
        if not self._public_secret_key_cache:
            self._public_secret_key_cache = Path(self.PUBLIC_SECRET_PATH).read_text()
        return self._public_secret_key_cache
        
def load_settings():
    load_dotenv(override=True)
    return Settings()

settings = load_settings()