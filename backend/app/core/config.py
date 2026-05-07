import secrets

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # maximum allowable waiting time after a failed task
    FAILURE_COOLDOWN_SEC: int

    # 3600 seconds * 24 hours * 7 days = 1 week
    ACCESS_TOKEN_EXPIRE_SEC: int = 60 * 60 * 24 * 7

    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @computed_field
    @property
    def REDIS_URL(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="redis",
            password=self.REDIS_PASSWORD,
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path='0',
        )

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    SQLALCHEMY_ECHO: bool = False

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    RABBITMQ_HOST: str
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_NODE_PORT: int = 5672

    @computed_field
    @property
    def RABBITMQ_URL(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="pyamqp",
            username=self.RABBITMQ_DEFAULT_USER,
            password=self.RABBITMQ_DEFAULT_PASS,
            host=self.RABBITMQ_HOST,
            port=self.RABBITMQ_NODE_PORT,
        )


settings = Settings()  # # pyright: ignore[reportCallIssue]
