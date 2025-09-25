import json
from fastapi import HTTPException
from redis.asyncio import Redis

from app.exceptions import HttpExc409Conflict
from app.redis.utils import redis_get_data
from app.config import settings
from app.users.utils import UserAuthRedisSchema

class RedisService:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        
     
    @staticmethod
    def validate_data(data):
        if not data:
            raise HTTPException(403, 'Нет ключа в redis')
    
    @staticmethod
    def validate_ttl(ttl):
        if not ttl > 0:
            raise HTTPException(403, 'Время жизни вышло')
    
    async def get_user_auth_data(self, key) -> UserAuthRedisSchema:
        ttl = await self.redis_client.ttl(key)
        self.validate_ttl(ttl)
        data = await redis_get_data(key)
        self.validate_data(data)
        # Увеличиваем попытку, чтобы пользователь не мог слишком часто 
        data['attempt'] += 1
        await self.redis_client.set(key, json.dumps(data), ex=ttl)
        
        return data
    
    
    async def validate_ip_limit(self, ip: str) -> None:
        '''Ограничение на получение кода по номеру телефона по ip'''
        
        if (await self.redis_client.get(f'limit_code_for_ip:{ip}')):
            raise HttpExc409Conflict('Должно пройти время для следующего получения кода')
    
    
    async def set_user_auth_data(self, user_identifier: str, data: UserAuthRedisSchema) -> None:
        await self.redis_client.set(
                    f"verify_code_user:{user_identifier}",
                    json.dumps(data),
                    ex=settings.VER_CODE_EXP_SEC,
                )
    
    
    async def get_dict(self, key: str) -> dict:
        redis_user_data = await self.redis_client.get(key)
            
        if not redis_user_data:
            return None
        
        data = json.loads(redis_user_data)
        return data


    async def delete(self, key: str) -> None:
        await self.redis_client.delete(key)
        
        
    async def set_limit_for_ip(self, ip: str):
        await self.redis_client.set(f'limit_code_for_ip:{ip}', json.dumps({'ip': ip}), ex=settings.LIMIT_SECONDS_GET_CODE)
        
    