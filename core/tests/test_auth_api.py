import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

@pytest.fixture
def api_client():
    client = APIClient()
    return client

@pytest.fixture
def user(db):
    # 패스워드는 반드시 create_user로 해시 생성
    return User.objects.create_user(
        username="test",
        email="t@example.com",
        password="test",
    )

@pytest.mark.django_db
def test_obtain_token_success(api_client, user, settings):
    # settings.REQUIRE_IDEMPOTENCY = False

    url = reverse("token_obtain_pair")
    payload = {"username": "test", "password": "test"}
    res = api_client.post(url, payload, format="json",  HTTP_X_TENANT_ID="public")
    
    assert res.status_code == 200, res.data
    assert "access" in res.data
    assert "refresh" in res.data

@pytest.mark.django_db
def test_obtain_token_invalid_password(api_client, user):
    url = reverse("token_obtain_pair")
    payload = {"username": "test", "password": "wrong"}
    res = api_client.post(url, payload, format="json")

    assert res.status_code == 400
