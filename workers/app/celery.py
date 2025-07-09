import os

from celery import Celery, Task
from celery.utils.log import get_task_logger
from google.api_core import exceptions as google_exceptions
from requests.exceptions import RequestException
from yt_dlp.utils import DownloadError

RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_NODE_PORT')

REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

broker_url = f'pyamqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/'
cache_url = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'


class CustomTask(Task):
    autoretry_for = (
        DownloadError,
        RequestException,
        google_exceptions.ResourceExhausted,
        google_exceptions.ServiceUnavailable,
        google_exceptions.DeadlineExceeded,
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

logger = get_task_logger(__name__)


if __name__ == '__main__':
    app.start()
