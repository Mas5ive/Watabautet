import json
from datetime import datetime, timedelta, timezone

from celery import states
from kombu import Connection
from redis import Redis
from sqlmodel import Session

from app import crud
from app.models import Summary, Video

VIDEO_LINK = 'v' * 11
CACHE_KEY_PREFIX: str = 'celery-task-meta-'


def create_video_in_db(
    session: Session,
    link: str = VIDEO_LINK,
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
    status: str = states.PENDING,
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
    cache_key = CACHE_KEY_PREFIX + task_id
    data = {
        'status': status,
        'result': result,
        'traceback': traceback,
        'children': children,
        'date_done': date_done,
        'task_id': task_id
    }
    cache.set(cache_key, json.dumps(data))


def get_item_from_cache(*, cache: Redis, task_id: str) -> dict | None:
    if value := cache.get(CACHE_KEY_PREFIX + task_id):
        task_result = json.loads(value.decode('utf-8'))
        return task_result


def get_data_from_message(task_queue: Connection.SimpleQueue) -> list[dict[str, str]] | None:
    """
    Retrieves data from the RabbitMQ message broker queue without blocking.
    A message will be deleted when received!

    Args:
        task_queue (Connection.SimpleQueue): The SimpleQueue instance connected to RabbitMQ.

    Returns:
        The payload data from the message if available, otherwise None.
    """
    try:
        message = task_queue.get(block=False)
        data = message.payload[0]
        message.ack()
    except task_queue.Empty:
        data = None
    return data


def get_formatted_time_offset(offset: int = 0, date_format: str = '%Y-%m-%dT%H:%M:%S.%f%z') -> str:
    """
    Calculates a time by adding an offset in seconds to the current UTC time,
    and returns it as a formatted string.

    Args:
        seconds_offset (int): The number of seconds to add to the current UTC time.
                        A positive value yields a future time, a negative value
                        yields a past time.
        date_format (str): The strftime format string for the output.
                     Defaults to '%Y-%m-%dT%H:%M:%S.%f%z'.

    Returns:
        str: A string representing the calculated UTC time, formatted according
        to date_format.
    """
    current_time_utc = datetime.now(timezone.utc)
    offset_time_utc = current_time_utc + timedelta(seconds=offset)
    return offset_time_utc.strftime(date_format)
