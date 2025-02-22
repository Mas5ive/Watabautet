from typing import Any

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (Message, Summary, SummaryPublic, UserCreate,
                        UserPublic, UserRegister)
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_name(session=session, name=user_in.name)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this name already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.post("/me/summaries", status_code=status.HTTP_201_CREATED, response_model=Message)
def save_summary_for_user(current_user: CurrentUser, session: SessionDep, summary: SummaryPublic) -> Any:
    """
    Creates a link between the user and the summary
    """
    summary_in_db = crud.get_summary_from_db(
        session=session,
        video_link=summary.video_link,
        size=summary.size,
        language=summary.language
    )

    if not summary_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The summary not found')

    validated_summary = Summary.model_validate(summary_in_db)
    user_summary = crud.get_user_with_summary(session=session, user=current_user, summary=validated_summary)

    if user_summary:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The summary already linked to the user')

    user_summary = crud.link_user_with_summary(session=session, user=current_user, summary=validated_summary)
    return Message(message='The summary successfully linked to the user')
