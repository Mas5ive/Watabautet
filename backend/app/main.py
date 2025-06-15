from contextlib import asynccontextmanager

import redis
from app.api.main import api_router
from app.core.config import settings
from celery import Celery
from fastapi import FastAPI
from fastapi.routing import APIRoute


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=0,
    )
    app.state.redis_con = redis.Redis(connection_pool=pool)
    app.state.celery = Celery('tasks', broker=str(settings.RABBITMQ_URL), backend=str(settings.REDIS_URL))

    yield

    app.state.redis_con.close()
    pool.disconnect()
    app.state.celery.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)


app.include_router(api_router, prefix=settings.API_V1_STR)
