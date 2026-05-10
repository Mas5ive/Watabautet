from typing import Annotated, Any

import structlog
from celery import states
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from app import crud
from app.api import utils
from app.api.deps import CeleryDep, CurrentUser, SessionDep
from app.core.config import settings
from app.models import Message, Summary, SummaryRequest, SummaryResponse, Video
from app.utils import calc_diff_curr_time

logger = structlog.get_logger()
router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get('/', responses={
    200: {'model': SummaryResponse},
    202: {'model': Message},
    404: {'model': Message},
    422: {'model': Message},
    503: {'model': Message},
})
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
    log = logger.bind(user_id=current_user.id, task_id=task_id_summary, video_link=request.video_link)
    task_data = celery.backend.get_task_meta(task_id_summary)
    summary = None

    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data) > 2:
        if task_data['status'] == states.SUCCESS:
            summary = SummaryResponse.model_validate(request, update=task_data['result'])
        elif task_data['status'] == states.FAILURE and 'ImpossibleTaskError' in task_data['traceback']:
            log.info('rejected', status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, reason='impossible_task')
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={'message': str(task_data['result'])}
            )
        elif task_data['status'] == states.FAILURE:
            diff_curr_time = calc_diff_curr_time(task_data['date_done'])
            sec_to_task_completion = settings.FAILURE_COOLDOWN_SEC - diff_curr_time

            if sec_to_task_completion > 0:
                log.warning(
                    'rejected', status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    reason='cooldown', retry_after=sec_to_task_completion
                )
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    headers={'Retry-After': f'{sec_to_task_completion}'},
                    content={'message': 'Some service is not working properly or is busy. Try the request again later'}
                )
        else:
            log.debug('in_progress', status_code=status.HTTP_202_ACCEPTED)
            return JSONResponse(status_code=202, content={'message': 'Getting the summary is in progress'})
    else:
        summary = crud.get_summary(
            session=session,
            video_link=request.video_link,
            size=request.size,
            language=request.language
        )

    if not summary:
        log.info('rejected', status_code=status.HTTP_404_NOT_FOUND, reason='not_in_storage')
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={'message': 'The summary not found'})

    log.info('succeeded', status_code=status.HTTP_200_OK)
    return summary


@router.post('/process', status_code=202, responses={
    202: {'model': Message},
    400: {'model': Message},
    503: {'model': Message}
})
def create_task_summary(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
    request: SummaryRequest,
) -> JSONResponse:
    """
    Creates a background task to process summary if no existing task is currently in progress or recently failed.
    There must be pre-existing data about the video on which the summarization is based.
    """
    task_id_summary = utils.TaskIdSummary.generate(
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )
    log = logger.bind(user_id=current_user.id, task_id=task_id_summary, video_link=request.video_link)
    task_data_summary = celery.backend.get_task_meta(task_id_summary)

    # If the length of task_data is <= 2, the task is not in the cache. And if it is not in the cache,
    # then it was never created. At the very bottom of the endpoint there is a call that writes the task metadata
    # into the cache. After that it has more than 2 metadata.
    if len(task_data_summary) > 2:
        if (
            task_data_summary['status'] == states.FAILURE and
            'ImpossibleTaskError' not in task_data_summary['traceback']
        ):
            diff_curr_time = calc_diff_curr_time(task_data_summary['date_done'])
            sec_to_task_completion = settings.FAILURE_COOLDOWN_SEC - diff_curr_time

            if sec_to_task_completion > 0:
                log.warning(
                    'rejected', status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    reason='cooldown', retry_after=sec_to_task_completion
                )
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    headers={'Retry-After': f'{sec_to_task_completion}'},
                    content={'message': 'Some service is not working properly or is busy. Try the request again later'}
                )
        else:
            log.info('rejected', status_code=status.HTTP_400_BAD_REQUEST, reason='task_already_exists')
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'The task already exists'})
    else:
        db_summary = crud.get_summary(
            session=session,
            video_link=request.video_link,
            size=request.size,
            language=request.language
        )

        if db_summary:
            log.info('rejected', status_code=status.HTTP_400_BAD_REQUEST, reason='already_in_db')
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The summary is already in the DB'}
            )

    task_id_video = utils.TaskIdVideo.generate(link=request.video_link)
    task_data_video = celery.backend.get_task_meta(task_id_video)

    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data_video) > 2 and task_data_video['status'] == states.SUCCESS:
        video = Video.model_validate({**task_data_video['result'], 'link': request.video_link})
    else:
        video = session.get(Video, request.video_link)

    if not video:
        log.info('rejected', status_code=status.HTTP_400_BAD_REQUEST, reason='no_video_data')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'There is no video data for this summary'}
        )

    context = structlog.contextvars.get_contextvars()
    celery.send_task(
        'app.tasks.make_summary', args=[request.model_dump(exclude={'video_link'}), video.model_dump()],
        headers={'request_id': context.get('request_id')}, task_id=task_id_summary,
    )
    celery.backend.store_result(task_id=task_id_summary, result=None, state=states.PENDING)
    log.info('succeeded', status_code=status.HTTP_202_ACCEPTED)
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
    task_id_summary = utils.TaskIdSummary.generate(
        video_link=request.video_link,
        size=request.size,
        language=request.language
    )
    log = logger.bind(user_id=current_user.id, task_id=task_id_summary, video_link=request.video_link)

    if crud.get_summary(
        session=session,
        video_link=request.video_link,
        size=request.size,
        language=request.language
    ):
        log.info('succeeded', status_code=status.HTTP_200_OK)
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The summary has already been saved'})

    task_data = celery.backend.get_task_meta(task_id_summary)
    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data) <= 2:
        log.info('rejected', status_code=status.HTTP_404_NOT_FOUND, reason='not_in_cache')
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': 'The summary was not found in the cache'}
        )

    if task_data['status'] != states.SUCCESS:
        log.info('rejected', status_code=status.HTTP_400_BAD_REQUEST, reason='task_not_complete')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The summary must be complete!'}
        )

    db_video = session.get(Video, request.video_link)

    if not db_video:
        log.info('rejected', status_code=status.HTTP_400_BAD_REQUEST, reason='no_video_data')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The parent video for this summary was not found in the database.'}
        )

    crud.create_obj(session=session, obj=Summary.model_validate(request, update=task_data['result']))
    log.info('succeeded', status_code=status.HTTP_201_CREATED)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The summary successfully saved'})
