import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

import app.tests.utils as t_utils
from app import crud
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Summary, User, UserRegister, UserSummary, Video

API_BASE_URL = f'{settings.API_V1_STR}/users'


class TestReadUserMe:

    API_ENDPOINT = f'{API_BASE_URL}/me'

    def test_read_authenticated_user(
        self, client: TestClient, userdata: dict[str, str], user_token_headers: dict[str, str]
    ) -> None:
        request = client.get(self.API_ENDPOINT, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        current_user = request.json()
        assert current_user
        assert current_user['name'] == userdata['name']

    def test_read_unauthenticated_user(self, client: TestClient) -> None:
        request = client.get(self.API_ENDPOINT)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestRegisterUser:

    API_ENDPOINT = f'{API_BASE_URL}/signup'

    @pytest.fixture()
    def data_for_register(self, db: Session):
        username = 'testuser'
        password = 'password'
        yield {'name': username, 'password': password}
        db.exec(delete(User).where(User.name == username))
        db.commit()

    def test_register_new_user(self, client: TestClient, db: Session, data_for_register: dict[str, str]) -> None:
        request = client.post(self.API_ENDPOINT, json=data_for_register)
        assert request.status_code == status.HTTP_201_CREATED
        response = request.json()
        assert response['name'] == data_for_register['name']
        user = db.exec(select(User).where(User.name == data_for_register['name'])).first()
        assert user

    def test_register_existing_user(self, client: TestClient, userdata: dict[str, str]) -> None:
        request = client.post(self.API_ENDPOINT, json=userdata)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['detail'] == 'The user with this name already exists in the system'


class TestDeleteUserMe:

    API_ENDPOINT = f'{API_BASE_URL}/me'

    @pytest.fixture()
    def new_user_data(self, client: TestClient, db: Session):
        username = 'testuser'
        password = 'password'
        user_in = UserRegister(name=username, password=password)
        user = User.model_validate(user_in, update={'hashed_password': get_password_hash(user_in.password)})
        user = crud.create_obj(session=db, obj=user)
        request = client.post(
            f'{settings.API_V1_STR}/login/access-token',
            data={'username': username, 'password': password}
        )
        response = request.json()
        auth_token = response['access_token']
        user_token_headers = {'Authorization': f'Bearer {auth_token}'}

        yield {'username': username, 'headers': user_token_headers}

        db.exec(delete(User).where(User.name == username))
        db.commit()

    def test_delete_authenticated_user(self, client: TestClient, db: Session, new_user_data: dict[str, str]) -> None:
        request = client.delete(self.API_ENDPOINT, headers=new_user_data['headers'])
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['message'] == 'User deleted successfully'
        result = db.exec(select(User).where(User.name == new_user_data['username'])).first()
        assert result is None

    def test_delete_unauthenticated_user(self, client: TestClient) -> None:
        request = client.delete(self.API_ENDPOINT)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestSaveSummaryForUser:

    API_ENDPOINT = f'{API_BASE_URL}/me/summaries'

    @pytest.fixture(scope='class', autouse=True)
    def db_summary(self, db: Session):
        t_utils.create_video_in_db(session=db)
        summary = t_utils.create_summary_in_db(session=db)
        yield summary.model_dump(exclude={'text'})
        db.exec(delete(Summary))
        db.exec(delete(Video))
        db.commit()

    @pytest.fixture(autouse=True)
    def cleanup_user_summary(self, db: Session):
        yield
        db.exec(delete(UserSummary))
        db.commit()

    def test_save_for_authenticated_user(
        self, db: Session, client: TestClient, userdata: dict[str, str], user_token_headers: dict[str, str],
        db_summary: dict[str, str]
    ) -> None:
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=db_summary)
        assert request.status_code == status.HTTP_201_CREATED
        response = request.json()
        assert response['message'] == 'The summary successfully linked to the user'

        user = db.exec(select(User).where(User.name == userdata['name'])).first()
        assert user is not None
        summary_in_db = db.exec(
            select(Summary).where(Summary.video_link == db_summary['video_link'])
        ).first()
        assert summary_in_db is not None
        user_summary = crud.get_user_with_summary(session=db, user=user, summary=summary_in_db)
        assert user_summary is not None

    def test_save_non_existing_summary(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        non_existing_summary_data = {
            'language': 'ru',
            'size': 'small',
            'video_link': 'w' * 11,
            'text': 'summary text'
        }
        request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=non_existing_summary_data)
        assert request.status_code == status.HTTP_404_NOT_FOUND
        response = request.json()
        assert response['detail'] == 'The summary not found'

    def test_save_summary_for_user_when_already_linked(
            self, client: TestClient, user_token_headers: dict[str, str], db_summary: dict[str, str]
    ) -> None:
        for _ in range(2):
            request = client.post(self.API_ENDPOINT, headers=user_token_headers, json=db_summary)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['detail'] == 'The summary already linked to the user'

    def test_save_summary_for_unauthenticated_user(self, client: TestClient, db_summary: dict[str, str]) -> None:
        request = client.post(self.API_ENDPOINT, json=db_summary)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteSummaryForUser:

    API_ENDPOINT = f'{API_BASE_URL}/me/summaries'

    @pytest.fixture
    def db_summary(self, db: Session, userdata: dict[str, str]):
        t_utils.create_video_in_db(session=db)
        summary = t_utils.create_summary_in_db(session=db)
        user = crud.get_user_by_name(session=db, name=userdata['name'])
        crud.link_user_with_summary(session=db, user=user, summary=summary)
        db.refresh(summary)
        yield summary.model_dump(exclude={'text'})
        db.exec(delete(UserSummary))
        db.exec(delete(Summary))
        db.exec(delete(Video))
        db.commit()

    def test_delete_for_authenticated_user(
            self, db: Session, client: TestClient, user_token_headers: dict[str, str], db_summary: dict[str, str]
    ) -> None:
        request = client.delete(self.API_ENDPOINT, headers=user_token_headers, params=db_summary)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert response['message'] == 'The user deleted the summary for himself'
        #  cascade deletion is set up, so both the video and the summary will be deleted.
        #  read more about this... from app import crud._delete_orphaned_entities_in_db
        assert db.exec(select(UserSummary)).first() is None
        assert db.exec(select(Summary)).first() is None
        assert db.exec(select(Video)).first() is None

    def test_delete_non_existing_summary(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        non_existing_summary_data = {
            'language': 'ru',
            'size': 'small',
            'video_link': 'w' * 11,
        }
        request = client.delete(self.API_ENDPOINT, headers=user_token_headers, params=non_existing_summary_data)
        assert request.status_code == status.HTTP_404_NOT_FOUND
        response = request.json()
        assert response['detail'] == 'The summary not found'

    def test_delete_non_linked_summary(
        self, db: Session, client: TestClient, user_token_headers: dict[str, str], db_summary: dict[str, str]
    ) -> None:
        db.exec(delete(UserSummary))
        db.commit()
        request = client.delete(self.API_ENDPOINT, headers=user_token_headers, params=db_summary)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
        response = request.json()
        assert response['detail'] == 'The user is not associated with the summary'

    def test_delete_for_unauthenticated_user(self, client: TestClient, db_summary: dict[str, str]) -> None:
        request = client.delete(self.API_ENDPOINT, params=db_summary)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUsersLibrary:

    API_ENDPOINT = f'{API_BASE_URL}/me/library'

    @pytest.fixture()
    def video_links(self, db: Session, userdata: dict[str, str]):
        video_link_1 = 'q' * 11
        video_link_2 = 'w' * 11
        user = crud.get_user_by_name(session=db, name=userdata['name'])
        t_utils.create_video_in_db(session=db, link=video_link_1)
        t_utils.create_video_in_db(session=db, link=video_link_2)
        summary_1 = t_utils.create_summary_in_db(session=db, video_link=video_link_1)
        summary_2 = t_utils.create_summary_in_db(session=db, video_link=video_link_1, size='large')
        summary_3 = t_utils.create_summary_in_db(session=db, video_link=video_link_2)
        crud.link_user_with_summary(session=db, user=user, summary=summary_1)
        crud.link_user_with_summary(session=db, user=user, summary=summary_2)
        crud.link_user_with_summary(session=db, user=user, summary=summary_3)
        yield (video_link_1, video_link_2)
        db.exec(delete(UserSummary))
        db.exec(delete(Summary))
        db.exec(delete(Video))
        db.commit()

    def test_get_for_authenticated_user(
            self, client: TestClient, user_token_headers: dict[str, str], video_links: tuple[str]
    ) -> None:
        request = client.get(self.API_ENDPOINT, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert 'videos' in response
        videos = response['videos']
        assert len(videos) == 2

        video_1 = next((v for v in videos if v['link'] == video_links[0]), None)
        assert video_1 is not None
        assert len(video_1['summaries']) == 2

        video_2 = next((v for v in videos if v['link'] == video_links[1]), None)
        assert video_2 is not None
        assert len(video_2['summaries']) == 1

    def test_get_empty_library(self, client: TestClient, user_token_headers: dict[str, str]) -> None:
        request = client.get(self.API_ENDPOINT, headers=user_token_headers)
        assert request.status_code == status.HTTP_200_OK
        response = request.json()
        assert 'videos' in response
        assert len(response['videos']) == 0

    def test_get_for_unauthenticated_user(self, client: TestClient) -> None:
        request = client.get(self.API_ENDPOINT)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED
