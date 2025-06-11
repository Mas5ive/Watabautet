from collections import defaultdict
from typing import Annotated, Any

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core.security import get_password_hash
from app.models import (Library, Message, SummaryRequest, SummaryView, User,
                        UserPublic, UserRegister, VideoForLibrary)
from fastapi import APIRouter, HTTPException, Query, status

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


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
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

    user = crud.create_obj(
        session=session,
        obj=User.model_validate(
            user_in, update={"hashed_password": get_password_hash(user_in.password)}
        ))
    return user


@router.post("/me/summaries", status_code=status.HTTP_201_CREATED, response_model=Message)
def save_summary_for_user(current_user: CurrentUser, session: SessionDep, request: SummaryRequest) -> Any:
    """
    Creates a link between the user and the summary
    """
    db_summary = crud.get_summary(
        session=session,
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )

    if not db_summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The summary not found')

    user_summary = crud.get_user_with_summary(session=session, user=current_user, summary=db_summary)

    if user_summary:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The summary already linked to the user')

    crud.link_user_with_summary(session=session, user=current_user, summary=db_summary)
    return Message(message='The summary successfully linked to the user')


@router.delete("/me/summaries", response_model=Message)
def delete_summary_for_user(
    current_user: CurrentUser,
    session: SessionDep,
    request: Annotated[SummaryRequest, Query()]
) -> Any:
    """
    Deletes a link between the user and the summary
    """
    db_summary = crud.get_summary(
        session=session,
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )

    if not db_summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The summary not found')

    user_summary = crud.get_user_with_summary(session=session, user=current_user, summary=db_summary)

    if not user_summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='The user is not associated with the summary'
        )

    crud.unlink_user_with_summary(session=session, user_summary=user_summary)
    return Message(message='The user deleted the summary for himself')


@router.get('/me/library', response_model=Library)
def get_users_library(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Gets all of the user's sammaries along with data about the videos on which they are made.
    """
    users_summaries = crud.get_users_summaries_with_video(session=session, user=current_user)

    videos_info = defaultdict(list)
    for summary in users_summaries:
        key = (summary.video.link, summary.video.title)
        summary_view = SummaryView.model_validate(summary)
        videos_info[key].append(summary_view)

    video_library = [
        VideoForLibrary(link=video_link, title=video_title, summaries=summaries)
        for (video_link, video_title), summaries in videos_info.items()
    ]
    return Library(videos=video_library)
