from typing import Annotated, Any

from app import crud
from app.api import utils
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.models import (Message, Summary, SummaryRequest, SummaryResponse,
                        TaskStatus)
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get('/', response_model=SummaryResponse)
def get_summary(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    request: Annotated[SummaryRequest, Query()],
) -> Any:
    """
    Get summary from cache or database. The summary taken from the cache may not be in a complete form,
    because it is there in the format of a certain stage of the task.
    """
    task_id_summary = utils.TaskIdSummary.generate(
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )
    task_result = utils.get_task_result(cache=cache, task_id=task_id_summary)

    if task_result:
        summary = utils.create_response_model(
            essential_fields=request.model_dump(),
            task_result=task_result,
            response_model=SummaryResponse
        )
    else:
        summary = crud.get_summary(
            session=session,
            video_link=request.video_link,
            size=request.size,
            language=request.language
        )

        if not summary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return summary


@router.post('/store', responses={
    200: {'model': Message},
    201: {'model': Message},
    400: {'model': Message},
    404: {'model': Message}
})
def save_summary(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    request: SummaryRequest
) -> JSONResponse:
    """
    Saves the summary from the cache in the DB.
    """
    summary_in_db = crud.get_summary(
        session=session,
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )

    if summary_in_db:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The summary has already been saved'})

    task_id_summary = utils.TaskIdSummary.generate(
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )

    task_result = utils.get_task_result(cache=cache, task_id=task_id_summary)

    if not task_result:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': 'The summary was not found in the cache'}
        )

    summary_in_cache = utils.create_response_model(
        essential_fields=request.model_dump(),
        task_result=task_result,
        response_model=SummaryResponse
    )

    if summary_in_cache.status != TaskStatus.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The summary must be complete!'}
        )

    summary_in_db = crud.create_summary(session=session, summary=Summary.model_validate(summary_in_cache))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The summary successfully saved'})
