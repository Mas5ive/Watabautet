from datetime import timedelta
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import Message, Token

logger = structlog.get_logger()
context = structlog.contextvars.get_contextvars()
router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    response: Response, session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Token is set in httpOnly cookie for security.
    """
    log = logger.bind(username=form_data.username)
    user = crud.authenticate(session=session, name=form_data.username, password=form_data.password)

    if not user:
        log.info('rejected', status_code=status.HTTP_400_BAD_REQUEST, reason='incorrect_credentials')
        raise HTTPException(status_code=400, detail='Incorrect name or password')

    log = log.bind(user_id=user.id)
    access_token_expires = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SEC)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)

    # Set token in httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_SEC,
        path="/",
    )

    log.info('succeeded', status_code=status.HTTP_200_OK)
    return Token(access_token=access_token)


@router.post("/logout")
def logout(response: Response, current_user: CurrentUser) -> Message:
    """
    Logout user by clearing the access_token cookie.
    """
    log = logger.bind(user_id=current_user.id)
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    log.info('succeeded', status_code=status.HTTP_200_OK)
    return Message(message="Successfully logged out")
