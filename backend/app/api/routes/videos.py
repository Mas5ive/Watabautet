from typing import Any

from app import crud
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.models import Message, SummaryPublic, Video
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get('/', response_model=Video)
def get_video(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    video_link: str
) -> Any:
    """
    Get video from cache or database
    """
    video = (
        crud.get_video_from_cache(cache=cache, video_link=video_link) or
        session.get(Video, video_link)
    )

    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return video


@router.post('/store', responses={200: {'model': Message}, 201: {'model': Message}, 400: {'model': Message}})
def save_video(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    summary: SummaryPublic
) -> JSONResponse:
    """
    Saves the video in a DB.
    """
    video_in_db = session.get(Video, summary.video_link)

    if video_in_db:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The video already exists'})

    video_in_cache = crud.get_video_from_cache(cache=cache, video_link=summary.video_link)

    if not video_in_cache:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'The video does not exist'})

    video_in_db = crud.create_video(session=session, video=video_in_cache)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The video successfully saved'})
