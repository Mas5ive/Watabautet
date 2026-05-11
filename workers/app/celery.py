import logging.config
import os
from typing import Any

import structlog
from celery import Celery, Task
from celery.signals import setup_logging as celery_setup_logging
from requests.exceptions import RequestException
from structlog.contextvars import merge_contextvars
from yt_dlp.utils import DownloadError

from app.exceptions import retriable_google_api_errors

LOG_ENV = os.getenv('LOG_ENV', 'dev')

if LOG_ENV not in ['dev', 'prod']:
    raise ValueError(f'Unknown logging environment: {LOG_ENV}')

RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_NODE_PORT')

REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

broker_url = f'pyamqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/'
cache_url = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'


@celery_setup_logging.connect
def on_setup_logging(**kwargs) -> None:
    # Common processors for structlog and standard logging
    shared_processors = [
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='iso', utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if LOG_ENV == 'dev':
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        log_level = 'DEBUG'
        broker_log_level = 'INFO'
    elif LOG_ENV == 'prod':
        renderer = structlog.processors.JSONRenderer()
        log_level = 'INFO'
        broker_log_level = 'WARNING'

    # Configure standard logging so that it sends everything to structlog
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structlog': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': renderer,
                'foreign_pre_chain': shared_processors,
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'structlog',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True,
            },
            'celery': {
                'handlers': ['default'],
                'level': 'WARNING',
                'propagate': False,
            },
            'amqp': {'level': broker_log_level},
            'kombu': {'level': broker_log_level},
        }
    })

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        cache_logger_on_first_use=True,
    )


class StructlogYTDLPLogger:
    def __init__(self, ydl: Any = None) -> None:
        self.logger = structlog.get_logger().bind(logger_name='yt-dlp')

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str, *, once: bool = False, only_once: bool = False) -> None:
        # Ignore specific non-critical warnings from yt-dlp
        for line in [
            "Unable to download webpage: HTTPSConnection(host='www.youtube.com'",
            "No supported JavaScript runtime could be found"
        ]:
            if line in message:
                return

        self.logger.warning(message)

    def error(self, message: str) -> None:
        # Reduce the level of certain errors
        for line in [
            "Unable to download API page: HTTPSConnection(host=\'www.youtube.com\'"
        ]:
            if line in message:
                self.logger.warning(message)
                return

        self.logger.error(message)

    def stdout(self, message: str) -> None:
        self.logger.info(message)

    def stderr(self, message: str) -> None:
        self.logger.error(message)


class CustomTask(Task):
    autoretry_for = (
        DownloadError,
        RequestException,
        *retriable_google_api_errors.values()
    )
    retry_backoff = True
    max_retries = int(os.getenv('CELERY_TASK_MAX_RETRIES', 8))
    retry_backoff_max = int(os.getenv('CELERY_TASK_BACKOFF_MAX', 600))
    retry_jitter = True


app = Celery('celery', task_cls=CustomTask, broker=broker_url, backend=cache_url, include=['app.tasks'])

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    result_expires=int(os.getenv('CELERY_RESULT_EXPIRES', 86400)),
    task_acks_late=True,
    task_acks_on_failure_or_timeout=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)

if __name__ == '__main__':
    app.start()
