import json
from fastapi import HTTPException
from app.redis.client import redis_client

async def redis_record_tries_with_ttl(key):
    ttl = await redis_client.ttl(key)
    
    if not ttl > 0:
        raise HTTPException(403, 'Время жизни вышло')
        
    data = await redis_get_data(key)
    validate(data)
    
    data['attempt'] += 1
    await redis_client.set(key, json.dumps(data), ex=ttl)
    
    return data

def validate(data):
    if not data:
        raise HTTPException(403, 'Нет ключа в redis')
    return True

async def redis_get_data(key):
    redis_user_data = await redis_client.get(key)
        
    if not redis_user_data:
        return None
    
    data = json.loads(redis_user_data)
    return data

async def redis_delete(key):
    redis_user_data = await redis_client.delete(key)
