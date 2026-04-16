from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings

API_BASE_URL = f'{settings.API_V1_STR}/login'


class TestLoginAccessToken:

    API_ENDPOINT = f'{API_BASE_URL}/access-token'

    def test_get_access_token(self, client: TestClient, userdata: dict[str, str]) -> None:
        login_data = {'username': userdata['name'], 'password': userdata['password']}
        request = client.post(self.API_ENDPOINT, data=login_data)
        tokens = request.json()
        assert request.status_code == status.HTTP_200_OK
        assert 'access_token' in tokens
        assert tokens['access_token']

    def test_get_access_token_incorrect_password(self, client: TestClient, userdata: dict[str, str]) -> None:
        login_data = {'username': userdata['name'], 'password': 'incorrect'}
        request = client.post(self.API_ENDPOINT, data=login_data)
        assert request.status_code == status.HTTP_400_BAD_REQUEST
