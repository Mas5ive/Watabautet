from typing import Annotated, Any

from app import crud
from app.api import utils
from app.api.deps import CacheDep, CurrentUser, SessionDep
from app.models import Message, TaskStatus, Video, VideoRequest, VideoResponse
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
    video_in_db = session.get(Video, request.link)

    if video_in_db:
        return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'The video has already been saved'})

    task_id_video = utils.TaskIdVideo.generate(link=request.link, major_language=request.major_language)
    task_result = utils.get_task_result(cache=cache, task_id=task_id_video)

    if not task_result:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': 'The video was not found in the cache'}
        )

    video_in_cache = utils.create_response_model(
        essential_fields=request.model_dump(),
        task_result=task_result,
        response_model=VideoResponse
    )

    if video_in_cache.status != TaskStatus.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'message': 'The video must be complete!'}
        )

    video_in_db = crud.create_video(session=session, video=Video.model_validate(video_in_cache))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'The video successfully saved'})
