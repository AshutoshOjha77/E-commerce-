# import redis.asyncio as redis 
# from confige import settings

# redis_client: redis.Redis | None = None

# async def init_redis():
#     global redis_client
#     redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True, max_connections= 20)
#     await redis_client.ping()
#     print("Redis connected successfully")

# async def close_redis():
#     global redis_client
#     if redis_client:
#         await redis_client.close()

# def get_redis() -> redis.Redis:
#     if redis_client is None:
#         raise RuntimeError("Redis is not intialized")
#     return redis_client


# import redis.asyncio as redis
# from confige import settings

# redis_client : redis.Redis | None = None

# async def init_redis():
#     global redis_client
#     redis_client = redis.from_url(settings.REDIS_URL, encoding = "utf-8", max_connection = 20)
#     await redis_client.ping()
#     print("Redis is connected successfully")

# async def close_redis():
#     global redis_client
#     if redis_client:
#         await redis_client.close()

# def get_redis() -> redis.Redis:
#     if redis_client is None:
#         raise RuntimeError("Redis is not intialized")
#     return redis_client

import redis.asyncio as redis
from confige import settings

redis_client : redis.Redis | None = None

async def init_redis():
    global redis_client
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True, max_connections=20)
    await redis_client.ping()
    print("Redis connected successfully")

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()

def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis is not initialized")
    return redis_client



