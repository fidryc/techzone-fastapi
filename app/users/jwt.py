from jwt import encode, decode
from jwt.exceptions import PyJWTError
from app.config import settings
from app.users.schema import UserSchema
from datetime import datetime, timedelta, timezone
from fastapi import Request, Response, HTTPException
import uuid
from app.logger import logger
from app.config import settings


def set_verify_register_token(response: Response, key: str):
    """Формирует и сохраняет токен в cookie для завершения регистрации"""
    payload = {
        "verify_register_key": str(key),
    }
    verify_register_token = encode(
        payload, key=settings.PRIVATE_SECRET_KEY, algorithm=settings.ALGORITM
    )
    response.set_cookie(
        settings.JWT_VERIFY_REGISTRATION_COOKIE_NAME, verify_register_token
    )


def get_verify_token(request: Request) -> dict:
    """Получает токен из cookie для завершения регистрации"""

    token = request.cookies.get(settings.JWT_VERIFY_REGISTRATION_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Не передан токен подтверждения регистрации.")
    try:
        token_payload: dict = decode(
            token,
            settings.PUBLIC_SECRET_KEY,
            settings.ALGORITM,
            options={"verify_exp": False},
        )
        if not token_payload.get("verify_register_key", None):
            raise HTTPException(401, "Неверный токен подтверждения.")
        return token_payload
    except Exception as e:
        raise HTTPException(
            401, "Ошибка декодировки токена подверждения регистрации"
        ) from e


def create_token(user: UserSchema, type: str) -> str:
    """Создает токены access и refresh"""
    jti = str(uuid.uuid4())
    if type == "access":
        time_exp = datetime.now(timezone.utc) + timedelta(seconds=settings.EXP_SEC)
    elif type == "refresh":
        time_exp = datetime.now(timezone.utc) + timedelta(
            days=settings.EXP_REFRESH_DAYS
        )

    payload = {
        "jti": jti,
        "user_email": str(user.email),
        "user_number": str(user.number),
        "user_role": str(user.role),
        "exp": time_exp.timestamp(),
        "type": str(type),
    }
    jwt = encode(payload, key=settings.PRIVATE_SECRET_KEY, algorithm=settings.ALGORITM)

    return jwt


def set_token(response: Response, user, type):
    """Создает и сохраняет в cookie access или refresh токен в cookie"""
    if type == "access":
        token = create_token(user, "access")
        response.set_cookie(settings.JWT_ACCESS_COOKIE_NAME, token, httponly=True)
    if type == "refresh":
        token = create_token(user, "refresh")
        response.set_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            token,
            httponly=True,
            max_age=int(timedelta(days=settings.EXP_REFRESH_DAYS).total_seconds()),
        )


def get_access_token(request: Request) -> dict:
    """Получает payload access токена из cookie"""
    token = request.cookies.get(settings.JWT_ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Нет токена для проверки аккаунт")
    try:
        payload: dict = decode(
            token,
            settings.PUBLIC_SECRET_KEY,
            settings.ALGORITM,
            options={"verify_exp": False},
        )
        if payload.get("type", None) != "access":
            raise HTTPException(401, "Токен access jwt подделан")
        return payload
    except PyJWTError:
        logger.warning(
            "Failed decode access jwt token", extra={"token": token}, exc_info=True
        )
        raise HTTPException(401, "Ошибка декодировки access токена")


def get_refresh_token(request: Request):
    """Получает payload refresh токена из cookie"""
    token = request.cookies.get(settings.JWT_REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "refresh token нет. Авторизуйтесь заново")
    try:
        payload: dict = decode(
            token,
            settings.PUBLIC_SECRET_KEY,
            settings.ALGORITM,
            options={"verify_exp": False},
        )
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Токен refresh подделан")
        return payload
    except:
        raise HTTPException(401, "Ошибка декодировки refresh")


def validate_payload_fields(token_payload: dict):
    """Проверка атрибутов payload токена на правильность типов"""
    jti = token_payload.get("jti", None)
    if not jti or not isinstance(jti, str):
        raise ValueError("неправильное поле jti")
    user_email = token_payload.get("user_email", None)
    user_number = token_payload.get("user_number", None)
    if (not user_email and not user_number) or (
        not (isinstance(user_email, str)) and not (isinstance(user_number, str))
    ):
        raise ValueError("неправильное поле user_email")
    user_role = token_payload.get("user_role", None)
    if not user_role or not isinstance(user_role, str):
        raise ValueError("неправильное поле user_role")
    exp = token_payload.get("exp", None)
    if not exp or not isinstance(exp, float):
        raise ValueError("неправильное поле exp")
    type = token_payload.get("type", None)
    if not type or type not in ("access", "refresh"):
        raise ValueError("неправильное поле type")


def validate_exp_token(payload: dict):
    """Проверяет не вышло ли время токена"""
    if datetime.now(timezone.utc).timestamp() > payload["exp"]:
        raise HTTPException(401, f"Время токена истекло {payload['type']}")
    return True
