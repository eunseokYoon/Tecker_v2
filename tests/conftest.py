import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authed_client():
    """인증된 APIClient 팩토리 픽스처. authed_client(user) 형태로 사용."""
    def _factory(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    return _factory
