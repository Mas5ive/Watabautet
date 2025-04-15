from typing import Annotated, Any

from app import crud
from app.api import utils
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.core.celery_client import celery_app
from app.core.config import settings
from app.models import (Message, Summary, SummaryRequest, SummaryResponse,
                        TaskStatus, Video, VideoRequest, VideoResponse)
from app.utils import calc_diff_curr_time
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


@router.post('/process', status_code=202, responses={
    202: {'model': Message},
    400: {'model': Message},
    503: {'model': Message}
})
def create_task_summary(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    summary_request: SummaryRequest,
    video_request: VideoRequest,
) -> JSONResponse:
    """
    Creates a background task to process summary if no existing task is currently in progress or recently failed.
    There must be pre-existing data about the video on which the summarization is based.
    """
    task_id_summary = utils.TaskIdSummary.generate(
        video_link=summary_request.video_link,
        size=summary_request.size,
        language=summary_request.language
    )
    task_result_summary = utils.get_task_result(cache=cache, task_id=task_id_summary)

    if task_result_summary:
        summary_in_cache = utils.create_response_model(
            essential_fields=summary_request.model_dump(),
            task_result=task_result_summary,
            response_model=SummaryResponse
        )

        if summary_in_cache.status == TaskStatus.PENDING:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'The task already exists'})
        elif summary_in_cache.status == TaskStatus.SUCCESS:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The summary is already in the cache'}
            )
        else:
            diff_curr_time = calc_diff_curr_time(summary_in_cache.details['date_done'])
            sec_to_task_completion = settings.FAILURE_COOLDOWN_SEC - diff_curr_time

            if sec_to_task_completion > 0:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    headers={'Retry-After': f'{sec_to_task_completion}'},
                    content={'message': 'Some service is not working properly or is busy. Try the request again later'}
                )
    else:
        summary_in_db = crud.get_summary(
            session=session,
            video_link=summary_request.video_link,
            size=summary_request.size,
            language=summary_request.language
        )

        if summary_in_db:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The summary is already in the DB'}
            )

    task_id_video = utils.TaskIdVideo.generate(link=video_request.link, major_language=video_request.major_language)
    task_result_video = utils.get_task_result(cache=cache, task_id=task_id_video)

    if task_result_video:
        video = utils.create_response_model(
            essential_fields=video_request.model_dump(),
            task_result=task_result_video,
            response_model=VideoResponse
        )
        if video.status != TaskStatus.SUCCESS:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'There is no data on this video yet'}
            )
    else:
        video = session.get(Video, video_request.link)

        if not video:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'There is no video data for this summary'}
            )

    celery_app.send_task(
        'app.tasks.make_summary',
        args=[summary_request.language, summary_request.size, video.model_dump()],
        task_id=task_id_summary
    )
    celery_app.backend.store_result(task_id=task_id_summary, result=None, state=TaskStatus.PENDING)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={'message': 'The task has been created!'})


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

    summary_in_db = crud.create_obj(session=session, obj=Summary.model_validate(summary_in_cache))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The summary successfully saved'})
