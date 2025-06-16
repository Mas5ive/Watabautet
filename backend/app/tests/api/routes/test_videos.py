import app.api.utils as utils
import app.tests.utils as t_utils
import pytest
from app.core.config import settings
from app.models import Video
from celery import states
from fastapi import status
from fastapi.testclient import TestClient
from redis import Redis
from sqlmodel import Session, delete

API_BASE_URL = f'{settings.API_V1_STR}/videos'


VIDEO_PARAMS = {
    'link': 'q' * 11,
    'major_language': 'ru'
}
COMMON_VIDEO_ATTRIBUTES = {
    'description': 'bla-bla',
    'text': 'bla-bla',
    'category': 'comedy',
    'title': 'wow'
}


class TestGetVideo:

    API_ENDPOINT = f'{API_BASE_URL}/'

    @pytest.fixture
    def db_video(self, db: Session):
        yield t_utils.create_video_in_db(session=db, **VIDEO_PARAMS, **COMMON_VIDEO_ATTRIBUTES)
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture
    def cache_video(self, cache: Redis):
        yield t_utils.create_item_in_cache(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.SUCCESS,
            result=COMMON_VIDEO_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        cache.flushall()

    def test_get_from_cache(self, client: TestClient, user_token_headers: dict[str, str], cache_video) -> None:
        request = client.get(self.API_ENDPOINT, params=VIDEO_PARAMS, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['category'] == COMMON_VIDEO_ATTRIBUTES['category']
        assert response['link'] == VIDEO_PARAMS['link']

    def test_get_from_db(self, client: TestClient, user_token_headers: dict[str, str], db_video) -> None:
        request = client.get(self.API_ENDPOINT, params=VIDEO_PARAMS, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['category'] == COMMON_VIDEO_ATTRIBUTES['category']
        assert response['link'] == VIDEO_PARAMS['link']

    def test_not_found(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        non_existent_video_params = {'link': 'x' * 11, 'major_language': 'en'}
        request = client.get(self.API_ENDPOINT, params=non_existent_video_params, headers=user_token_headers)
        assert request.status_code == status.HTTP_404_NOT_FOUND

    def test_get_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.get(self.API_ENDPOINT, params=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestSaveVideo:

    API_ENDPOINT = f'{API_BASE_URL}/store'

    @pytest.fixture
    def db_video(self, db: Session):
        return t_utils.create_video_in_db(session=db, **VIDEO_PARAMS, **COMMON_VIDEO_ATTRIBUTES)

    @pytest.fixture(autouse=True)
    def delete_db_video(self, db: Session):
        yield
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture
    def cache_video(self, cache: Redis):
        yield t_utils.create_item_in_cache
        cache.flushall()

    def test_save_video(
            self, db: Session, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.SUCCESS,
            result=COMMON_VIDEO_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_201_CREATED
        response = request.json()
        assert response['message'] == 'The video successfully saved'
        video = db.get(Video, VIDEO_PARAMS['link'])
        assert video is not None
        assert video.link == VIDEO_PARAMS['link']
        assert video.category == COMMON_VIDEO_ATTRIBUTES['category']

    def test_save_exixisting_video_in_db(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, db_video
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.SUCCESS,
            result=COMMON_VIDEO_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['message'] == 'The video has already been saved'

    def test_not_found(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        non_existent_video_params = {'link': 'x' * 11, 'major_language': 'en'}
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=non_existent_video_params)
        assert request.status_code == status.HTTP_404_NOT_FOUND
        response = request.json()
        assert response['message'] == 'The video was not found in the cache'

    def test_save_unsuccessful_task(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.PENDING,
            result=None,
            date_done=None
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The video must be complete!'

    def test_save_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.post(self.API_ENDPOINT, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateTaskVideo:

    API_ENDPOINT = f'{API_BASE_URL}/process'

    @pytest.fixture
    def db_video(self, db: Session):
        yield t_utils.create_video_in_db(session=db, **VIDEO_PARAMS, **COMMON_VIDEO_ATTRIBUTES)
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture
    def cache_video(self):
        return t_utils.create_item_in_cache

    @pytest.fixture(autouse=True)
    def cleanup_cache(self, cache: Redis):
        yield
        cache.flushall()

    def test_create_for_new_video(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], task_queue
    ) -> None:
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_202_ACCEPTED
        response = request.json()
        assert response['message'] == 'The task has been created!'
        video_data = t_utils.get_data_from_message(task_queue)[0]
        assert video_data == VIDEO_PARAMS
        task_id = utils.TaskIdVideo.generate(**VIDEO_PARAMS)
        task_result = utils.get_task_result(cache=cache, task_id=task_id)
        assert task_result is not None
        assert task_result['status'] == states.PENDING
        assert task_result['result'] is None

    def test_create_when_task_is_in_cache_with_status_pending(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, task_queue
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS)
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The task already exists'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_when_task_is_in_cache_with_status_success(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, task_queue
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.SUCCESS,
            result=COMMON_VIDEO_ATTRIBUTES,
            date_done='2025-03-26T19:13:53.395702+00:00'
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The video is already in the cache'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_when_task_is_in_cache_with_status_failed(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, task_queue
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.FAILURE,
            result={
                'exc_type': 'Exception',
                'exc_message': [],
                'exc_module': 'builtins'
            },
            date_done=t_utils.get_formatted_time_offset()
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        response = request.json()
        assert response['message'] == 'Some service is not working properly or is busy. Try the request again later'
        assert 'Retry-After' in request.headers
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_create_when_task_is_in_cache_with_status_failed_but_cooled_down(
            self, cache: Redis, client: TestClient, user_token_headers: dict[str, str], cache_video, task_queue
    ) -> None:
        cache_video(
            cache=cache,
            task_id=utils.TaskIdVideo.generate(**VIDEO_PARAMS),
            status=states.FAILURE,
            result={
                'exc_type': 'Exception',
                'exc_message': [],
                'exc_module': 'builtins'
            },
            date_done=t_utils.get_formatted_time_offset(offset=-settings.FAILURE_COOLDOWN_SEC)
        )
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_202_ACCEPTED
        response = request.json()
        assert response['message'] == 'The task has been created!'
        video_data = t_utils.get_data_from_message(task_queue)[0]
        assert video_data == VIDEO_PARAMS

    def test_create_for_existing_video_in_db(
            self, client: TestClient, user_token_headers: dict[str, str], db_video, task_queue
    ) -> None:
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['message'] == 'The video is already in the DB'
        message_data = t_utils.get_data_from_message(task_queue)
        assert message_data is None

    def test_save_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.post(self.API_ENDPOINT, json=VIDEO_PARAMS)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED
