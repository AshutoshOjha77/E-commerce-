from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis_client import init_redis, close_redis
from elastic_client import init_elasticsearch, close_elasticsearch
from databases import engine, base
import router

base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await init_elasticsearch()
    yield
    await close_redis()
    await close_elasticsearch()


app = FastAPI(title="The production of E-commerce site", lifespan=lifespan)
app.include_router(router.router)