from typing import Annotated, Any

from app import crud
from app.api import utils
from app.api.deps import CacheDep, CeleryDep, CurrentUser, SessionDep
from app.core.config import settings
from app.models import Message, TaskStatus, Video, VideoRequest, VideoResponse
from app.utils import calc_diff_curr_time
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get('/', response_model=VideoResponse)
def get_video(
    current_user: CurrentUser,
    session: SessionDep,
    cache: CacheDep,
    request: Annotated[VideoRequest, Query()],
) -> Any:
    """
    Get video from cache or database. The video taken from the cache may not be in a complete form,
    because it is there in the format of a certain stage of the task.
    """
    task_id_video = utils.TaskIdVideo.generate(link=request.link, major_language=request.major_language)
    task_result = utils.get_task_result(cache=cache, task_id=task_id_video)

    if task_result:
        video = utils.create_response_model(
            essential_fields=request.model_dump(),
            task_result=task_result,
            response_model=VideoResponse
        )
    else:
        video = session.get(Video, request.link)

        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return video


@router.post('/process', status_code=202, responses={
    202: {'model': Message},
    400: {'model': Message},
    503: {'model': Message}
})
def create_task_video(
    current_user: CurrentUser,
    session: SessionDep,
    celery: CeleryDep,
    cache: CacheDep,
    request: VideoRequest
) -> JSONResponse:
    """
    Creates a background task to process video data if no existing task is currently in progress or recently failed
    """
    task_id_video = utils.TaskIdVideo.generate(link=request.link, major_language=request.major_language)
    task_result = utils.get_task_result(cache=cache, task_id=task_id_video)

    if task_result:
        cache_video = utils.create_response_model(
            essential_fields=request.model_dump(),
            task_result=task_result,
            response_model=VideoResponse
        )

        if cache_video.status == TaskStatus.PENDING:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'The task already exists'})
        elif cache_video.status == TaskStatus.SUCCESS:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The video is already in the cache'}
            )
        else:
            diff_curr_time = calc_diff_curr_time(cache_video.details['date_done'])
            sec_to_task_completion = settings.FAILURE_COOLDOWN_SEC - diff_curr_time

            if sec_to_task_completion > 0:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    headers={'Retry-After': f'{sec_to_task_completion}'},
                    content={'message': 'Some service is not working properly or is busy. Try the request again later'}
                )
    else:
        db_video = session.get(Video, request.link)

        if db_video:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'message': 'The video is already in the DB'}
            )

    celery.send_task('app.tasks.get_video_data', args=[request.model_dump()], task_id=task_id_video)
    celery.backend.store_result(task_id=task_id_video, result=None, state=TaskStatus.PENDING)
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
    cache: CacheDep,
    request: VideoRequest
) -> JSONResponse:
    """
    Saves the video from the cache in the DB.
    """
    db_video = session.get(Video, request.link)

    if db_video:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The video has already been saved'})

    task_id_video = utils.TaskIdVideo.generate(link=request.link, major_language=request.major_language)
    task_result = utils.get_task_result(cache=cache, task_id=task_id_video)

    if not task_result:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': 'The video was not found in the cache'}
        )

    cache_video = utils.create_response_model(
        essential_fields=request.model_dump(),
        task_result=task_result,
        response_model=VideoResponse
    )

    if cache_video.status != TaskStatus.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The video must be complete!'}
        )

    db_video = crud.create_obj(session=session, obj=Video.model_validate(cache_video))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The video successfully saved'})
