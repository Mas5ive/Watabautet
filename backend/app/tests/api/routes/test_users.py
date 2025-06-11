import pytest
from app.core.config import settings
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

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


