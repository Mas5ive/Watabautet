import logging
import uuid
from contextlib import asynccontextmanager

import structlog
from celery import Celery
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from prometheus_fastapi_instrumentator import Instrumentator
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

from app.api.main import api_router
from app.core.config import settings

if settings.LOG_ENV not in ['dev', 'prod']:
    raise ValueError(f'Unknown logging environment: {settings.LOG_ENV}')


def custom_generate_unique_id(route: APIRoute) -> str:
    if not route.tags:
        return route.name
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.celery = Celery('tasks', broker=str(settings.RABBITMQ_URL), backend=str(settings.REDIS_URL))
    yield
    app.state.celery.close()


def setup_logging() -> None:
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    if settings.LOG_ENV == 'dev':
        logging.root.setLevel(logging.DEBUG)
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        wrapper_class = structlog.make_filtering_bound_logger(logging.DEBUG)
    elif settings.LOG_ENV == 'prod':
        logging.root.setLevel(logging.INFO)
        renderer = structlog.processors.JSONRenderer()
        wrapper_class = structlog.make_filtering_bound_logger(logging.INFO)

    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer
        ],
        wrapper_class=wrapper_class,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

print('wow')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3500",  # Frontend development server
        "http://frontend:3500",   # Frontend in docker network
        "http://localhost:80",    # Frontend production
        "http://frontend",        # Frontend service name
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware('http')
async def logging_middleware(request: Request, call_next):
    clear_contextvars()
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)

    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger = structlog.get_logger()
        logger.exception('unhandled_runtime_error', error=str(exc))

        if settings.LOG_ENV == 'dev':
            raise exc

        return JSONResponse(
            status_code=500,
            content={'message': 'Internal Server Error'}
        )

# Instrument the application and export the /metrics endpoint.
# If this is a multi-process mode, the metrics from all workers will be aggregated.
Instrumentator().instrument(app).expose(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
