from fastapi import FastAPI
from app.users.router import router as users_router
from app.redis.client import redis_client

app = FastAPI()

app.include_router(users_router)

