from typing import Annotated, Generator

import jwt
from celery import Celery
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)


def extract_token(
    token_from_header: Annotated[str | None, Depends(reusable_oauth2)] = None,
    access_token: Annotated[str | None, Cookie(include_in_schema=False)] = None,
) -> str:
    """
    Extract JWT token from either access_token cookie or Authorization header.
    """
    # 1. Try to get token from header (Standard for Swagger UI flow)
    if token_from_header:
        return token_from_header

    # 2. Try to get token from cookie (Standard for web/frontend flow)
    if access_token:
        if access_token.startswith("Bearer "):
            return access_token[7:]
        return access_token

    if not access_token and not token_from_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


TokenDep = Annotated[str, Depends(extract_token)]


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_celery() -> Celery:
    from app.main import app
    celery = app.state.celery
    return celery


CeleryDep = Annotated[Celery, Depends(get_celery)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
