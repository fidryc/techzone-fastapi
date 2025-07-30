import json
from fastapi import HTTPException
from app.redis.client import redis_client

async def redis_rerecord_tries_with_ttl(key):
    ttl = await redis_client.ttl(key)
    
    if not ttl > 0:
        raise HTTPException(401, 'Введите сначала свои данные')
        
    data = await redis_get_data(key)
    validate(data)
    
    data['try'] += 1
    await redis_client.set(key, json.dumps(data), ex=ttl)
    
    return data

def validate(data):
    if not data:
        raise HTTPException(401, 'Введите свои данные')
    return True

async def redis_get_data(key):
    redis_user_data = await redis_client.get(key)
        
    if not redis_user_data:
        raise HTTPException(403, 'Введите сначала свои данные')
    
    data = json.loads(redis_user_data)
    
    return data

