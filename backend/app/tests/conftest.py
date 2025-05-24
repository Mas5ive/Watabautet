from collections.abc import Generator
from typing import Any

from kombu.simple import SimpleQueue
import pytest
from app.core.config import settings
from app.core.db import engine
from app.core.security import get_password_hash
from app.crud import create_obj
from app.main import app
from app.models import User, UserRegister
from fastapi.testclient import TestClient
from kombu import Connection
from redis import Redis
from sqlmodel import Session, delete


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def cache() -> Generator[Redis, Any, None]:
    cache = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD, db=0)
    yield cache
    cache.close()


@pytest.fixture(scope="session", autouse=True)
def task_queue() -> Generator[SimpleQueue, Any, None]:
    with Connection(str(settings.RABBITMQ_URL)) as con:
        queue = con.SimpleQueue('celery')
        yield queue


@pytest.fixture(scope='module')
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def userdata(db: Session) -> Generator[dict[str, str], Any, None]:
    user_data = UserRegister(name='test_name', password='test_password')
    create_obj(
        session=db,
        obj=User.model_validate(
            user_data, update={"hashed_password": get_password_hash(user_data.password)}
        ))

    yield user_data.model_dump()

    db.exec(delete(User))
    db.commit()


@pytest.fixture(scope='module')
def user_token_headers(client: TestClient, userdata: dict[str, str]) -> dict[str, str]:
    login_data = {'username': userdata['name'], 'password': userdata['password']}
    request = client.post(f'{settings.API_V1_STR}/login/access-token', data=login_data)
    response = request.json()
    auth_token = response['access_token']
    headers = {'Authorization': f'Bearer {auth_token}'}
    return headers
