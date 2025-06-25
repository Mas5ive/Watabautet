import app.api.utils as utils
import app.tests.utils as t_utils
import pytest
from app import crud
from app.core.config import settings
from app.models import Summary, Video
from celery import states
from fastapi import status
from fastapi.testclient import TestClient
from redis import Redis
from sqlmodel import Session, delete

API_BASE_URL = f'{settings.API_V1_STR}/summaries'


VIDEO_LINK = 'q' * 11
COMMON_VIDEO_ATTRIBUTES = {
    'description': 'bla-bla',
    'text': 'bla-bla',
    'category': 'comedy',
    'title': 'wow'
}

SUMMARY_PARAMS = {
    'video_link': VIDEO_LINK,
    'size': 'small',
    'language': 'ru'
}
COMMON_SUMMARY_ATTRIBUTES = {'text': 'something interesting'}


class TestGetSummary:

    API_ENDPOINT = f'{API_BASE_URL}/'

    @pytest.fixture(scope='class', autouse=True)
    def db_video(self, db: Session):
        yield t_utils.create_video_in_db(session=db, link=VIDEO_LINK)
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture
    def db_summary(self, db: Session):
        yield t_utils.create_summary_in_db(session=db, **SUMMARY_PARAMS,  **COMMON_SUMMARY_ATTRIBUTES)
        db.exec(delete(Summary))
        db.commit()

    @pytest.fixture
    def cache_summary(self, cache: Redis):
        yield t_utils.create_item_in_cache
        cache.flushall()

    def test_get_from_cache(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_summary
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.SUCCESS,
            result=COMMON_SUMMARY_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.get(self.API_ENDPOINT, params=SUMMARY_PARAMS, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['text'] == COMMON_SUMMARY_ATTRIBUTES['text']
        assert response['video_link'] == SUMMARY_PARAMS['video_link']

    def test_get_from_db(
            self, client: TestClient, user_token_headers: dict[str, str], db_summary
    ) -> None:
        request = client.get(self.API_ENDPOINT, params=SUMMARY_PARAMS, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['text'] == COMMON_SUMMARY_ATTRIBUTES['text']
        assert response['video_link'] == SUMMARY_PARAMS['video_link']

    def test_not_found(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        non_existent_summary_params = {'video_link': 'x' * 11, 'language': 'en', 'size': 'small'}
        request = client.get(self.API_ENDPOINT, params=non_existent_summary_params, headers=user_token_headers)
        assert request.status_code == status.HTTP_404_NOT_FOUND

    def test_get_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.get(self.API_ENDPOINT, params=SUMMARY_PARAMS)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestSaveSummary:

    API_ENDPOINT = f'{API_BASE_URL}/store'

    @pytest.fixture(scope='class', autouse=True)
    def db_video(self, db: Session):
        yield t_utils.create_video_in_db(session=db, link=VIDEO_LINK)
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture
    def db_summary(self, db: Session):
        return t_utils.create_summary_in_db(session=db, **SUMMARY_PARAMS,  **COMMON_SUMMARY_ATTRIBUTES)

    @pytest.fixture(autouse=True)
    def delete_db_summary(self, db: Session):
        yield
        db.exec(delete(Summary))
        db.commit()

    @pytest.fixture
    def cache_summary(self, cache: Redis):
        yield t_utils.create_item_in_cache
        cache.flushall()

    def test_save_from_cache(
            self, db: Session, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_summary
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.SUCCESS,
            result=COMMON_SUMMARY_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=SUMMARY_PARAMS)
        assert request.status_code == status.HTTP_201_CREATED
        response = request.json()
        assert response['message'] == 'The summary successfully saved'
        summary = crud.get_summary(session=db, **SUMMARY_PARAMS)
        assert summary is not None
        assert summary.video_link == SUMMARY_PARAMS['video_link']
        assert summary.text == COMMON_SUMMARY_ATTRIBUTES['text']

    def test_save_exixisting_summary_in_db(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_summary, db_summary
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.SUCCESS,
            result=COMMON_SUMMARY_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=SUMMARY_PARAMS)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['message'] == 'The summary has already been saved'

    def test_not_found(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        non_existent_summary_params = {'video_link': 'x' * 11, 'language': 'en', 'size': 'small'}
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=non_existent_summary_params)
        assert request.status_code == status.HTTP_404_NOT_FOUND
        response = request.json()
        assert response['message'] == 'The summary was not found in the cache'

    def test_save_unsuccessful_task(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_summary
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.PENDING,
            result=None,
            date_done=None
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=SUMMARY_PARAMS)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The summary must be complete!'

    def test_save_when_parent_video_isnt_in_db(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_summary
    ) -> None:
        summary_params = {'video_link': 'x' * 11, 'language': 'en', 'size': 'small'}
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**summary_params),
            status=states.SUCCESS,
            result=COMMON_SUMMARY_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=summary_params)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The parent video for this summary was not found in the database.'

    def test_save_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.post(self.API_ENDPOINT, json=SUMMARY_PARAMS)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateTaskSummary:

    API_ENDPOINT = f'{API_BASE_URL}/process'

    @pytest.fixture
    def db_video(self, db: Session):
        yield t_utils.create_video_in_db(session=db, link=VIDEO_LINK)
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture
    def db_summary(self, db: Session):
        yield t_utils.create_summary_in_db(session=db, **SUMMARY_PARAMS,  **COMMON_SUMMARY_ATTRIBUTES)
        db.exec(delete(Summary))
        db.commit()

    @pytest.fixture
    def cache_summary(self):
        return t_utils.create_item_in_cache

    @pytest.fixture
    def cache_video(self):
        yield t_utils.create_item_in_cache

    @pytest.fixture(autouse=True)
    def cleanup_cache(self, cache: Redis):
        yield
        cache.flushall()

    def test_create_when_parent_video_is_in_cache_with_status_success(
        self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, task_queue
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(link=VIDEO_LINK),
            status=states.SUCCESS,
            result=COMMON_VIDEO_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_202_ACCEPTED
        response = request.json()
        assert response['message'] == 'The task has been created!'
        summary_data, video_data = t_utils.get_data_from_message(task_queue)
        assert summary_data['language'] == SUMMARY_PARAMS['language']
        assert summary_data['size'] == SUMMARY_PARAMS['size']
        assert video_data == {'link': VIDEO_LINK,  **COMMON_VIDEO_ATTRIBUTES}
        task_id = utils.TaskIdSummary.generate(**SUMMARY_PARAMS)
        task_result = t_utils.get_item_from_cache(cache=cache, task_id=task_id)
        assert task_result is not None
        assert task_result['status'] == states.PENDING
        assert task_result['result'] is None

    def test_create_when_parent_video_is_in_cache_with_non_success_status(
        self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, task_queue
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(link=VIDEO_LINK),
            status=states.PENDING,
        )
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'There is no video data for this summary'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None
        task_id = utils.TaskIdSummary.generate(**SUMMARY_PARAMS)
        task_result = t_utils.get_item_from_cache(cache=cache, task_id=task_id)
        assert task_result is None

    def test_create_when_parent_video_is_in_db(
        self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], db_video, task_queue
    ) -> None:
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_202_ACCEPTED
        response = request.json()
        assert response['message'] == 'The task has been created!'
        summary_data, video_data = t_utils.get_data_from_message(task_queue)
        assert summary_data['language'] == SUMMARY_PARAMS['language']
        assert summary_data['size'] == SUMMARY_PARAMS['size']
        assert video_data == {'link': VIDEO_LINK,  **COMMON_VIDEO_ATTRIBUTES}
        task_id = utils.TaskIdSummary.generate(**SUMMARY_PARAMS)
        task_result = t_utils.get_item_from_cache(cache=cache, task_id=task_id)
        assert task_result is not None
        assert task_result['status'] == states.PENDING
        assert task_result['result'] is None

    def test_create_when_parent_video_does_not_exist(
        self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], task_queue
    ) -> None:
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'There is no video data for this summary'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None
        task_id = utils.TaskIdSummary.generate(**SUMMARY_PARAMS)
        task_result = t_utils.get_item_from_cache(cache=cache, task_id=task_id)
        assert task_result is None

    def test_create_when_task_is_in_cache_with_status_pending(
        self, cache: Redis, client: Redis, user_token_headers: dict[str, str], db_video, cache_summary, task_queue
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.PENDING
        )
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The task already exists'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_when_task_is_in_cache_with_status_success(
        self, cache: Redis, client: Redis, user_token_headers: dict[str, str], db_video, cache_summary, task_queue
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.SUCCESS,
            result=COMMON_SUMMARY_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The summary is already in the cache'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_when_task_is_in_cache_with_status_failed(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], db_video, cache_summary,
            task_queue
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.FAILURE,
            result={
                'exc_type': 'Exception',
                'exc_message': [],
                'exc_module': 'builtins'
            },
            date_done=t_utils.get_formatted_time_offset()
        )
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        response = request.json()
        assert response['message'] == 'Some service is not working properly or is busy. Try the request again later'
        assert 'Retry-After' in request.headers
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_when_task_is_in_cache_with_status_failed_but_cooled_down(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_summary,
            task_queue, db_video
    ) -> None:
        cache_summary(
            cache=cache,
            task_id=utils.TaskIdSummary.generate(**SUMMARY_PARAMS),
            status=states.FAILURE,
            result={
                'exc_type': 'Exception',
                'exc_message': [],
                'exc_module': 'builtins'
            },
            date_done=t_utils.get_formatted_time_offset(offset=-settings.FAILURE_COOLDOWN_SEC)
        )
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_202_ACCEPTED
        response = request.json()
        assert response['message'] == 'The task has been created!'
        summary_data, video_data = t_utils.get_data_from_message(task_queue)
        assert summary_data['language'] == SUMMARY_PARAMS['language']
        assert summary_data['size'] == SUMMARY_PARAMS['size']
        assert video_data == {'link': VIDEO_LINK,  **COMMON_VIDEO_ATTRIBUTES}

    def test_create_for_existing_summary_in_db(
            self, client: TestClient, user_token_headers: dict[str, str], db_video, db_summary, task_queue
    ) -> None:
        request = client.post(
            self.API_ENDPOINT,
            headers=user_token_headers,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The summary is already in the DB'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.post(
            self.API_ENDPOINT,
            json={'summary_request': SUMMARY_PARAMS, 'video_request': {'link': VIDEO_LINK}}
        )
        assert request.status_code == status.HTTP_401_UNAUTHORIZED
