import json
from app import crud
from app.core.config import settings
from app.models import Summary, Video
from app.models import TaskStatus
from redis import Redis
from sqlmodel import Session

VIDEO_LINK = 'v' * 11


def create_video_in_db(
    session: Session,
    link: str = VIDEO_LINK,
    major_language: str = 'ru',
    description: str = 'bla-bla',
    text: str = 'bla-bla',
    category: str = 'comedy',
    title: str = 'wow'
) -> Video:
    """
    Creates a video object in the database using provided data and default values.
    """

    video = crud.create_obj(session=session, obj=Video(
        link=link,
        major_language=major_language,
        description=description,
        text=text,
        category=category,
        title=title
    ))
    return video


def create_summary_in_db(
        session: Session,
        language: str = 'ru',
        size: str = 'small',
        video_link: str = VIDEO_LINK,
        text: str = 'summary text'
) -> Summary:
    """
    Creates a summary object in the database using provided data and default values.
    """

    summary = crud.create_obj(session=session, obj=Summary(
        language=language,
        size=size,
        video_link=video_link,
        text=text
    ))
    return summary


def create_item_in_cache(
    cache: Redis,
    task_id: str,
    status: TaskStatus = TaskStatus.PENDING,
    result: dict | None = None,
    traceback: str | None = None,
    children: list | None = None,
    date_done: str | None = None

) -> None:
    """
    Creates a task item in the Redis cache with the specified status and data.

    Note:

    Some examples showing possible data in the cache:

    PENDING:
    ```{
        "status": "PENDING",
        "result": null,
        "traceback": null,
        "children": null,
        "date_done": null,
        "task_id": "32fb09c1-0317-538e-9a06-9c6f3ceabe18"
    }
    ```

    FAILURE:
    ```{
        "status": "FAILURE",
        "result": {
            "exc_type": "Exception",
            "exc_message": [],
            "exc_module": "builtins"
        },
        "traceback": "Traceback (most recent call last):  File /workers/.venv/lib/python3.13...",
        "children": [],
        "date_done": "2022-03-26T19:08:35.809483+00:00",
        "task_id": "32fb09c1-0317-538e-9a06-9c6f3ceabe18"
    }
    ```

    SUCCESS:
    ```{
        "status": "SUCCESS",
        "result": {
            "field1": "text",
            "field2": "text"
        },
        "traceback": null,
        "children": [],
        "date_done": "2022-03-26T19:13:53.395702+00:00",
        "task_id": "32fb09c1-0317-538e-9a06-9c6f3ceabe18"
    }
    ```
    """
    cache_key = settings.CACHE_KEY_PREFIX + task_id
    data = {
        'status': status,
        'result': result,
        'traceback': traceback,
        'children': children,
        'date_done': date_done,
        'task_id': task_id
    }
    cache.set(cache_key, json.dumps(data))


