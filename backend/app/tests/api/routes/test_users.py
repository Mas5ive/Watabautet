from app.core.config import settings
from fastapi import status
from fastapi.testclient import TestClient

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


