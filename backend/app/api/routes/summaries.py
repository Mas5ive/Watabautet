from typing import Any

from app import crud
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.models import Message, SummaryPublic
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

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


@router.post("/store", responses={200: {'model': Message}, 201: {'model': Message}, 400: {'model': Message}})
def save_summary(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    summary: SummaryPublic
) -> JSONResponse:
    """
    Saves the summary in a DB.
    """
    summary_in_db = crud.get_summary_from_db(
        session=session,
        video_link=summary.video_link,
        size=summary.size,
        language=summary.language
    )

    if summary_in_db:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The summary already exists'})

    summary_in_cache = crud.get_summary_from_cache(
        cache=cache,
        video_link=summary.video_link,
        size=summary.size,
        language=summary.language
    )

    if not summary_in_cache:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'The summary does not exist'})

    summary_in_db = crud.create_summary(session=session, summary=summary_in_cache)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The summary successfully saved'})


@router.delete('/store', response_model=Message)
def delete_summary(session: SessionDep, current_user: CurrentUser, summary: SummaryPublic) -> Any:
    """
    Deletes the summary from the database only if it is not saved by any user.
    """
    summary_in_db = crud.get_summary_from_db(
        session=session,
        video_link=summary.video_link,
        size=summary.size,
        language=summary.language
    )
    if not summary_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The summary not found')

    if summary_in_db.user_summaries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='This summary cannot be deleted because someone else has it'
        )

    summary_in_db = crud.delete_summary(session=session, summary=summary_in_db)
    return Message(message='The summary successfully deleted')
