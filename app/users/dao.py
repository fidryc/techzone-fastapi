from app.dao import BaseDao
from app.users.models import User, RefreshTokenBL
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.logger import create_msg_db_error, logger


class UserDao(BaseDao):
    model = User

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_user(self, email, number):
        user_by_email = None
        user_by_number = None

        if email:
            user_by_email = await self.find_by_filter(email=email)
        if number:
            user_by_number = await self.find_by_filter(number=number)
        if user_by_email or user_by_number:
            logger.warning(
                "User already exists", extra={"email": email, "number": number}
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с такой почтой или номером телефона уже существует",
            )

    async def find_user(self, email, number):
        try:
            user_by_email = await self.find_by_filter(email=email)
        except SQLAlchemyError as e:
            msg = create_msg_db_error("Failed find user by email")
            logger.error(msg, extra={"email": email}, exc_info=True)
            raise HTTPException(
                status_code=500, detail="Ошибка при поиске пользователя по email"
            ) from e

        try:
            user_by_number = await self.find_by_filter(number=number)
        except SQLAlchemyError:
            msg = create_msg_db_error("Failed find user by number")
            logger.error(msg, extra={"number": number}, exc_info=True)
            raise HTTPException(
                status_code=500, detail="Ошибка при поиске пользователя по номеру"
            )

        if user_by_email:
            logger.info("User found by email", extra={"email": email})
            return user_by_email[0]
        if user_by_number:
            logger.info("User found by number", extra={"number": number})
            return user_by_number[0]

        logger.warning("User not found", extra={"email": email, "number": number})
        return None

    async def delete_user(self, user_id: int):
        try:
            query = text(
                """
            DELETE FROM users
            WHERE user_id = :user_id
            """
            )
            result = await self.session.execute(query, params={"user_id": user_id})
            logger.info(
                "User deleted successfully",
                extra={"user_id": user_id, "rows_affected": result.rowcount},
            )
        except SQLAlchemyError as e:
            msg = create_msg_db_error("Failed to delete user")
            logger.error(msg, extra={"user_id": user_id}, exc_info=True)
            raise HTTPException(
                status_code=500, detail="Ошибка при удалении пользователя"
            ) from e


class RefreshTokenBLDao(BaseDao):
    model = RefreshTokenBL

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_refresh_token_bl(self, jti) -> str:
        try:
            token = await self.find_by_filter_one(jti=jti)
            if token:
                logger.info("Refresh token found in blacklist", extra={"jti": jti})
            else:
                logger.debug("Refresh token not found in blacklist", extra={"jti": jti})
            return token
        except SQLAlchemyError as e:
            msg = create_msg_db_error("Cannot find rfbl token")
            logger.error(msg, extra={"jti": jti}, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка в базе данных в RefreshTokenBL таблице",
            ) from e
        except Exception as e:
            msg = create_msg_db_error("Unexpected error in get_refresh_token_bl")
            logger.error(msg, extra={"jti": jti}, exc_info=True)
            raise HTTPException(
                status_code=500, detail="Неожиданная ошибка при проверке refresh token"
            ) from e
