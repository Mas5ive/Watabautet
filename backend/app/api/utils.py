import json
import uuid
from typing import Type, TypeVar

from app.core.config import settings
from app.models import SummaryResponse, TaskStatus, VideoResponse
from redis import Redis


class _TaskId:
    """
    A base class for generating unique task identifiers using UUID version 5.

    Attributes:
        _namespace (UUID): A predefined UUID namespace used to generate deterministic UUIDs.

    Methods:
        generate(*args: str) -> str:
            Generates a UUID based on the provided arguments using UUIDv5.
    """

    _namespace = uuid.UUID('1bc4e60e-cf57-4d75-a2be-df44aabc1134')

    @classmethod
    def generate(cls, *args: str) -> str:
        """
        Generates a unique task identifier.

        Args:
            *args (str): A variable number of string arguments to create a deterministic UUID.

        Returns:
            str: The generated UUIDv5 string.
        """
        key = '|'.join(args)
        return str(uuid.uuid5(cls._namespace, key))


class TaskIdSummary(_TaskId):
    """
    A class for generating unique summary task identifiers.

    Methods:
        generate(video_link: str, size: str, language: str) -> str:
            Generates a UUID based on video link, size, and language.
    """

    @classmethod
    def generate(cls, *, video_link: str, size: str, language: str) -> str:
        """
        Generates a unique summary task identifier.

        Args:
            video_link (str): The video link to be summarized.
            size (str): The size of the summary.
            language (str): The language of the summary.

        Returns:
            str: The generated UUIDv5 string.
        """
        return super().generate(video_link, size, language)


class TaskIdVideo(_TaskId):
    """
    A class for generating unique video task identifiers.

    Methods:
        generate(link: str) -> str:
            Generates a UUID based on the video link.
    """

    @classmethod
    def generate(cls, *, link: str, major_language: str) -> str:
        """
        Generates a unique video task identifier.

        Args:
            link (str): The video link.
            major_language (str): the main language in the video.

        Returns:
            str: The generated UUIDv5 string.
        """
        return super().generate(link, major_language)


def get_task_result(*, cache: Redis, task_id: str) -> dict | None:
    if value := cache.get(settings.CACHE_KEY_PREFIX + task_id):
        task_result = json.loads(value.decode('utf-8'))
        return task_result


_ResponseModel = TypeVar('_ResponseModel', SummaryResponse, VideoResponse)


def create_response_model(
    *,
    essential_fields: dict,
    task_result: dict,
    response_model: Type[_ResponseModel],
) -> _ResponseModel:
    """
    Generates an instance of the Pydantic response model (`SummaryResponse` or `VideoResponse`) based
    on the result of the background task and mandatory fields.

    Depending on the task status (`TaskStatus`), the behavior is as follows:
    - **SUCCESS**: fields from `task_result[“result”]` (e.g. `text`, `title`, `description`) are added.
    - **FAILURE**: details of the error are added as `details`, including `date_done` and `exc_message`.
    - **PENDING**: status only with no additional data.

    Arguments:
        essential_fields (dict): Fields required to be included in the response,
        task_result (dict): A dictionary containing the result of the background task Celery:
            {
                "status": "SUCCESS" | "FAILURE" | "PENDING",
                "result": {...}, # structure depends on status
                "date_done": str, # when FAILURE
            }
        response_model (Type[_ResponseModel]): Pydantic model into which the response will be assembled.

    Returns:
        _ResponseModel: an instance of `SummaryResponse` or `VideoResponse` containing the merged data.

    Exceptions:
        ValueError: If `task_result['status']` is not a valid value of `TaskStatus`.
    """
    try:
        status = TaskStatus(task_result['status'])
    except ValueError:
        raise ValueError(f"Incorrect task status: {task_result['status']}")

    other_fields = {'status': status}

    if status == TaskStatus.SUCCESS:
        other_fields.update(task_result['result'])

    if status == TaskStatus.FAILURE:
        other_fields.update({
            'details': {
                'date_done': task_result['date_done'],
                'exc_message': task_result['result']['exc_message']
            }
        })

    return response_model(**essential_fields, **other_fields)
