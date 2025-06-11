import app.api.utils as utils
import app.tests.utils as t_utils
import pytest
from app.core.config import settings
from app.models import TaskStatus, Video
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
            status=TaskStatus.SUCCESS,
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
            status=TaskStatus.SUCCESS,
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
            status=TaskStatus.SUCCESS,
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
            status=TaskStatus.PENDING,
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


