from pydantic_settings import BaseSettings
from pydantic import FilePath
from pathlib import Path
from dotenv import load_dotenv



class Settings(BaseSettings):
    DB_HOST: str
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
    REDIS_PORT: int
    
    VER_CODE_EXP_SEC: int
    
    MAX_TRIES_EMAIL_CODE: int
    
    class Config:
        env_file = '.env'
        
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