from typing import Any

from app import crud
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.models import Video
from fastapi import APIRouter, HTTPException, status

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
