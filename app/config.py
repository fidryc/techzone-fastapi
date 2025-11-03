from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, FilePath
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import NullPool


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "PROD"]
    LOG_LEVEL: Literal["INFO", "DEBUG", "WARNING", "ERROR"]

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_NAME: str
    TEST_DB_USER: str
    TEST_DB_PASS: str

    PROD_DB_HOST: str
    PROD_DB_PORT: int
    PROD_DB_NAME: str
    PROD_DB_USER: str
    PROD_DB_PASS: str

    PRIVATE_SECRET_PATH: FilePath
    PUBLIC_SECRET_PATH: FilePath

    ALGORITM: str
    EXP_SEC: int
    EXP_REFRESH_DAYS: int
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str

    REDIS_HOST_: str
    REDIS_PORT_: int

    PROD_REDIS_HOST: str
    PROD_REDIS_PORT: int

    TEST_REDIS_HOST: str
    TEST_REDIS_PORT: int

    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str

    RABBITMQ_HOST: str
    RABBITMQ_HOST_PROD: str
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

    model_config = ConfigDict(env_file=".env")

    _private_secret_key_cache: str | None = None
    _public_secret_key_cache: str | None = None

    @property
    def PRIVATE_SECRET_KEY(self) -> str:
        if not self._private_secret_key_cache:
            self._private_secret_key_cache = Path(self.PRIVATE_SECRET_PATH).read_text()
        return self._private_secret_key_cache

    @property
    def PUBLIC_SECRET_KEY(self) -> str:
        if not self._public_secret_key_cache:
            self._public_secret_key_cache = Path(self.PUBLIC_SECRET_PATH).read_text()
        return self._public_secret_key_cache

    @property
    def DB_URL(self):
        DB_URLS = {
            "TEST": f"postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}",
            "PROD": f"postgresql+asyncpg://{self.PROD_DB_USER}:{self.PROD_DB_PASS}@{self.PROD_DB_HOST}:{self.PROD_DB_PORT}/{self.PROD_DB_NAME}",
            "DEV": f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}",
        }
        return DB_URLS[self.MODE]

    @property
    def DB_PARAMS(self):
        DB_URLS = {"TEST": {"poolclass": NullPool}, "PROD": {}, "DEV": {}}
        return DB_URLS[self.MODE]

    @property
    def DB_SYNC_URL(self):
        DB_SYNC_URLS = {
            "TEST": f"postgresql://{settings.TEST_DB_USER}:{settings.TEST_DB_PASS}@{settings.TEST_DB_HOST}:{settings.TEST_DB_PORT}/{settings.TEST_DB_NAME}",
            "PROD": f"postgresql://{settings.PROD_DB_USER}:{settings.PROD_DB_PASS}@{settings.PROD_DB_HOST}:{settings.PROD_DB_PORT}/{settings.PROD_DB_NAME}",
            "DEV": f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
        }
        return DB_SYNC_URLS[self.MODE]

    @property
    def REDIS_URL(self):
        REDIS_URLS = {
            "TEST": f"redis://{settings.TEST_REDIS_HOST}:{settings.TEST_REDIS_PORT}",
            "PROD": f"redis://{settings.PROD_REDIS_HOST}:{settings.PROD_REDIS_PORT}",
            "DEV": f"redis://{settings.REDIS_HOST_}:{settings.REDIS_PORT_}",
        }
        return REDIS_URLS[settings.MODE]

    @property
    def REDIS_HOST(self):
        return {
            "TEST": self.TEST_REDIS_HOST,
            "DEV": self.REDIS_HOST_,
            "PROD": self.PROD_REDIS_HOST,
        }[settings.MODE]

    @property
    def REDIS_PORT(self):
        return {
            "TEST": self.TEST_REDIS_PORT,
            "DEV": self.REDIS_PORT_,
            "PROD": self.PROD_REDIS_PORT,
        }[settings.MODE]

    @property
    def REDIS_DB(self):
        return {"TEST": 15, "DEV": 0, "PROD": 0}[settings.MODE]


def load_settings():
    load_dotenv(override=True)
    return Settings()


settings = load_settings()
