from typing import Any

from app import crud
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.models import SummaryPublic
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get('/', response_model=SummaryPublic)
def get_summary(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    video_link: str,
    size: str,
    language: str,
) -> Any:
    """
    Get summary from cache or database
    """
    summary = (
        crud.get_summary_from_cache(cache=cache, video_link=video_link, size=size, language=language) or
        crud.get_summary_from_db(session=session, video_link=video_link, size=size, language=language)
    )

    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    summary = SummaryPublic.model_validate(summary)
    return summary
