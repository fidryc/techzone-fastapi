import json
from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from app.redis.utils import redis_get_data
from app.config import settings
from app.users.utils import UserAuthRedisSchema, verify_code
from app.logger import logger


class RedisService:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
     
    @staticmethod
    def validate_data(data):
        """Проверка, что data не None"""
        if not data:
            logger.warning('No data found in Redis')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Нет ключа в redis'
            )
   
    @staticmethod
    def validate_ttl(ttl):
        """Проверка, что время жизни не истекло"""
        if not ttl > 0:
            logger.warning('Redis key TTL expired', extra={'ttl': ttl})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Время жизни вышло'
            )
   
    async def get_user_auth_data(self, key) -> UserAuthRedisSchema:
        """
        Получение данных пользователя для регистрации из redis
       
        Получение данных с увеличением количества попыток входа.
        Выставлением значения по ключу, чтобы можно было попытаться войти еще раз,
        если код будет неверным
        """
        try:
            logger.debug('Getting user auth data from Redis', extra={'key': key})
            
            ttl = await self.redis_client.ttl(key)
            self.validate_ttl(ttl)
            
            data = await redis_get_data(key)
            self.validate_data(data)
            
            # Увеличиваем попытку, чтобы пользователь не мог слишком часто пытаться ввести код
            data['attempt'] += 1
            await self.redis_client.set(key, json.dumps(data), ex=ttl)
            
            logger.debug('User auth data retrieved', extra={'key': key, 'attempt': data['attempt']})
            return data
            
        except HTTPException:
            raise
        except RedisError as e:
            logger.error('Redis error getting user auth data', extra={'key': key}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при работе с Redis'
            )
        except Exception as e:
            logger.error('Unexpected error getting user auth data', extra={'key': key}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении данных'
            )
   
    async def set_user_auth_data(self, user_identifier: str, data: UserAuthRedisSchema) -> None:
        """Сохраняет данные для регистрации пользователя в redis"""
        try:
            key = f"verify_code_user:{user_identifier}"
            await self.redis_client.set(
                key,
                json.dumps(data),
                ex=settings.VER_CODE_EXP_SEC,
            )
            logger.info('User auth data saved to Redis', extra={'user_identifier': user_identifier, 'ttl': settings.VER_CODE_EXP_SEC})
        except RedisError as e:
            logger.error('Redis error saving user auth data', extra={'user_identifier': user_identifier}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при сохранении данных в Redis'
            ) from e
        except Exception as e:
            logger.error('Unexpected error saving user auth data', extra={'user_identifier': user_identifier}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при сохранении данных'
            )
   
    async def get_dict(self, key: str) -> dict:
        """
        Возвращает dict из redis по ключу
       
        Возвращает dict из redis, если значение по ключу есть, либо None, если нет.
        """
        try:
            redis_user_data = await self.redis_client.get(key)
            
            if not redis_user_data:
                logger.debug('Key not found in Redis', extra={'key': key})
                return None
            
            data = json.loads(redis_user_data)
            logger.debug('Data retrieved from Redis', extra={'key': key})
            return data
            
        except RedisError as e:
            logger.error('Redis error getting dict', extra={'key': key}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при получении данных из Redis'
            )
        except json.JSONDecodeError as e:
            logger.error('JSON decode error', extra={'key': key}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при декодировании данных'
            )
        except Exception as e:
            logger.error('Unexpected error getting dict from Redis', extra={'key': key}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Непредвиденная ошибка при получении данных'
            )

    async def delete(self, key: str) -> None:
        """Удаление ключа из Redis"""
        try:
            await self.redis_client.delete(key)
            logger.debug('Key deleted from Redis', extra={'key': key})
        except RedisError as e:
            logger.error('Redis error deleting key', extra={'key': key}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при удалении данных из Redis'
            )
       
    async def _validate_ip_limit(self, ip: str) -> None:
        """Ограничение на получение кода для регистрации по ip"""
        try:
            if await self.redis_client.get(f'limit_code_for_ip:{ip}'):
                logger.warning('IP rate limit exceeded', extra={'ip': ip})
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail='Должно пройти время для следующей попытки регистрации'
                )
        except HTTPException :
            raise
        except RedisError as e:
            logger.error('Redis error validating IP limit', extra={'ip': ip}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при проверке лимита IP'
            ) from e
         
    async def _set_limit_for_ip(self, ip: str):
        """Сохраняет данные о получении кода по ip"""
        try:
            await self.redis_client.set(
                f'limit_code_for_ip:{ip}',
                json.dumps({'ip': ip}),
                ex=settings.LIMIT_SECONDS_GET_CODE
            )
            logger.info('IP limit set', extra={'ip': ip, 'ttl': settings.LIMIT_SECONDS_GET_CODE})
        except RedisError as e:
            logger.error('Redis error setting IP limit', extra={'ip': ip}, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при установке лимита IP'
            ) from e
       
    async def processing_limit_ip(self, ip: str):
        """Обработка ограничения получения кодов по ip"""
        logger.debug('Processing IP limit', extra={'ip': ip})
        await self._validate_ip_limit(ip)
        await self._set_limit_for_ip(ip)
         
    @staticmethod
    def is_correct_attempt(attempt: int) -> bool:
        """Проверяет, что текущая попытка не превышает максимальную"""
        return attempt < settings.MAX_TRIES_EMAIL_CODE  
   
    async def validate_user_auth_data(self, data: UserAuthRedisSchema, code_from_user: int, redis_key: str) -> None:
        """Валидирует данные для регистрации в redis"""
        try:
            if not self.is_correct_attempt(data['attempt']):
                logger.warning('Max attempts exceeded', extra={'attempts': data['attempt']})
                await self.delete(redis_key)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Количество попыток вышло. Попробуйте зарегистрироваться ещё раз'
                )
            
            if not verify_code(code_from_user, data['code']):
                logger.warning('Invalid verification code provided', extra={'attempt': data['attempt']})
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='Передан неверный код'
                )
                
            logger.debug('User auth data validated successfully')
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Unexpected error validating user auth data', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при валидации данных'
            )