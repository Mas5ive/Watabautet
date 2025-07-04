from typing import Annotated, Any

from app import crud
from app.api import utils
from app.api.deps import CeleryDep, CurrentUser, SessionDep
from app.core.config import settings
from app.models import Message, Video, VideoRequest, VideoResponse
from app.utils import calc_diff_curr_time
from celery import states
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get('/', responses={
    200: {'model': VideoResponse},
    202: {'model': Message},
    422: {'model': Message},
    503: {'model': Message},
})
def get_video(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
    request: Annotated[VideoRequest, Query()],
) -> Any:
    """
    Get video from cache or database. The video in the cache must have a successful completion status to be taken.
    """
    task_id_video = utils.TaskIdVideo.generate(link=request.link)
    task_data = celery.backend.get_task_meta(task_id_video)
    video = None
    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data) > 2:
        if task_data['status'] == states.SUCCESS:
            video = VideoResponse.model_validate(request, update=task_data['result'])
        elif task_data['status'] == states.FAILURE and 'ImpossibleTaskError' in task_data['traceback']:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={'message': str(task_data['result'])}
            )
        elif task_data['status'] == states.FAILURE:
            diff_curr_time = calc_diff_curr_time(task_data['date_done'])
            sec_to_task_completion = settings.FAILURE_COOLDOWN_SEC - diff_curr_time

            if sec_to_task_completion > 0:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    headers={'Retry-After': f'{sec_to_task_completion}'},
                    content={'message': 'Some service is not working properly or is busy. Try the request again later'}
                )
        else:
            return JSONResponse(status_code=202, content={'message': 'Getting the video is in progress'})
    else:
        video = session.get(Video, request.link)

    if video:
        return video
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post('/process', status_code=202, responses={
    202: {'model': Message},
    400: {'model': Message},
    503: {'model': Message}
})
def create_task_video(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
    request: VideoRequest
) -> JSONResponse:
    """
    Creates a background task to process video data if no existing task is currently in progress or recently failed
    """
    task_id_video = utils.TaskIdVideo.generate(link=request.link)
    task_data = celery.backend.get_task_meta(task_id_video)

    # If the length of task_data is <= 2, the task is not in the cache. And if it is not in the cache,
    # then it was never created. At the very bottom of the endpoint there is a call that writes the task metadata
    # into the cache. After that it has more than 2 metadata.
    if len(task_data) > 2:
        if task_data['status'] == states.FAILURE and 'ImpossibleTaskError' not in task_data['traceback']:
            diff_curr_time = calc_diff_curr_time(task_data['date_done'])
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
        db_video = session.get(Video, request.link)

        if db_video:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The video is already in the DB'}
            )

    celery.send_task('app.tasks.get_video_data', args=[request.model_dump()], task_id=task_id_video)
    celery.backend.store_result(task_id=task_id_video, result=None, state=states.PENDING)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={'message': 'The task has been created!'})


@router.post('/store', responses={
    200: {'model': Message},
    201: {'model': Message},
    400: {'model': Message},
    404: {'model': Message}
})
def save_video(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
    request: VideoRequest
) -> JSONResponse:
    """
    Saves the video from the cache in the DB.
    """
    db_video = session.get(Video, request.link)

    if db_video:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The video has already been saved'})

    task_id_video = utils.TaskIdVideo.generate(link=request.link)
    task_data = celery.backend.get_task_meta(task_id_video)

    # If the length of task_data is <= 2, the task is not in the cache.
    if len(task_data) <= 2:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': 'The video was not found in the cache'}
        )

    if task_data['status'] != states.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The video must be complete!'}
        )

    db_video = crud.create_obj(session=session, obj=Video.model_validate(request, update=task_data['result']))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The video successfully saved'})
