from typing import Annotated, Any

from app import crud
from app.api import utils
from app.api.deps import CeleryDep, CurrentUser, SessionDep
from app.core.config import settings
from app.models import (Message, Summary, SummaryRequest, SummaryResponse,
                        Video, VideoRequest)
from app.utils import calc_diff_curr_time
from celery import states
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get('/', response_model=SummaryResponse)
def get_summary(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
    request: Annotated[SummaryRequest, Query()],
) -> Any:
    """
    Get summary from cache or database. The summary in the cache must have a successful completion status to be taken.
    """
    task_id_summary = utils.TaskIdSummary.generate(
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )
    task_data = celery.backend.get_task_meta(task_id_summary)

    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data) > 2 and task_data['status'] == states.SUCCESS:
        summary = SummaryResponse.model_validate(request, update=task_data['result'])
    else:
        summary = crud.get_summary(
            session=session,
            video_link=request.video_link,
            size=request.size,
            language=request.language
        )

    if summary:
        return summary
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post('/process', status_code=202, responses={
    202: {'model': Message},
    400: {'model': Message},
    503: {'model': Message}
})
def create_task_summary(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
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
    task_data_summary = celery.backend.get_task_meta(task_id_summary)

    # If the length of task_data is <= 2, the task is not in the cache. And if it is not in the cache,
    # then it was never created. At the very bottom of the endpoint there is a call that writes the task metadata
    # into the cache. After that it has more than 2 metadata.
    if len(task_data_summary) > 2:
        if task_data_summary['status'] == states.SUCCESS:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The summary is already in the cache'}
            )

        elif task_data_summary['status'] == states.FAILURE:
            diff_curr_time = calc_diff_curr_time(task_data_summary['date_done'])
            sec_to_task_completion = settings.FAILURE_COOLDOWN_SEC - diff_curr_time

            if sec_to_task_completion > 0:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    headers={'Retry-After': f'{sec_to_task_completion}'},
                    content={'message': 'Some service is not working properly or is busy. Try the request again later'}
                )
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'The task already exists'})
    else:
        summary = crud.get_summary(
            session=session,
            video_link=summary_request.video_link,
            size=summary_request.size,
            language=summary_request.language
        )

        if summary:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The summary is already in the DB'}
            )

    task_id_video = utils.TaskIdVideo.generate(link=video_request.link)
    task_data_video = celery.backend.get_task_meta(task_id_video)

    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data_video) > 2 and task_data_video['status'] == states.SUCCESS:
        video = Video.model_validate(video_request, update=task_data_video['result'])
    else:
        video = session.get(Video, video_request.link)

    if not video:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'There is no video data for this summary'}
        )

    celery.send_task(
        'app.tasks.make_summary',
        args=[summary_request.model_dump(exclude={'video_link'}), video.model_dump()],
        task_id=task_id_summary
    )
    celery.backend.store_result(task_id=task_id_summary, result=None, state=states.PENDING)
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
    celery: CeleryDep,
    request: SummaryRequest
) -> JSONResponse:
    """
    Saves the summary from the cache in the DB.
    """
    db_summary = crud.get_summary(
        session=session,
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )

    if db_summary:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The summary has already been saved'})

    task_id_summary = utils.TaskIdSummary.generate(
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )
    task_data = celery.backend.get_task_meta(task_id_summary)

    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data) <= 2:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': 'The summary was not found in the cache'}
        )

    if task_data['status'] != states.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The summary must be complete!'}
        )

    db_video = session.get(Video, request.video_link)

    if not db_video:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The parent video for this summary was not found in the database.'}
        )

    db_summary = crud.create_obj(session=session, obj=Summary.model_validate(request, update=task_data['result']))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The summary successfully saved'})
