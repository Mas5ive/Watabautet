from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.models import Message, Token

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    response: Response, session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Token is set in httpOnly cookie for security.
    """
    user = crud.authenticate(
        session=session, name=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail='Incorrect name or password')
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    # Set token in httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        path="/",
    )

    return Token(access_token=access_token)


@router.post("/logout")
def logout(response: Response) -> Message:
    """
    Logout user by clearing the access_token cookie.
    """
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    return Message(message="Successfully logged out")
