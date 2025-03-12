from app.core.config import settings
from celery import Celery

celery_app = Celery('tasks', broker=str(settings.RABBITMQ_URL), backend=str(settings.REDIS_URL))
