import pytest
import responses as responses_lib
from rest_framework.test import APIClient

from tests.factories import UserFactory

GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"


@pytest.fixture
def api():
    return APIClient()


# ──────────────────────────────────────────────────────────
# Case 1: 신규 Google 사용자 → User 생성 + access + refresh body 반환
# ──────────────────────────────────────────────────────────
@responses_lib.activate
@pytest.mark.django_db
def test_new_google_user_is_created(api):
    responses_lib.add(
        responses_lib.GET,
        GOOGLE_TOKENINFO,
        json={
            "sub": "google-new-1",
            "email": "alice@example.io",
            "email_verified": "true",
            "aud": "test-client-id",
            "name": "Alice",
        },
    )

    res = api.post("/auth/google/", {"id_token": "stub-token"}, format="json")

    assert res.status_code == 200
    assert "access" in res.json()
    assert "refresh" in res.json()   # body에 refresh 토큰 포함 확인

    from apps.accounts.models import User
    assert User.objects.filter(google_sub="google-new-1").exists()


# ──────────────────────────────────────────────────────────
# Case 2: 기존 사용자(google_sub 일치) → 동일 user_id 반환
# ──────────────────────────────────────────────────────────
@responses_lib.activate
@pytest.mark.django_db
def test_existing_user_linked_by_google_sub(api):
    user = UserFactory(google_sub="google-existing-1", email="bob@example.io")

    responses_lib.add(
        responses_lib.GET,
        GOOGLE_TOKENINFO,
        json={
            "sub": "google-existing-1",
            "email": "bob@example.io",
            "email_verified": "true",
            "aud": "test-client-id",
        },
    )

    res = api.post("/auth/google/", {"id_token": "stub-token"}, format="json")

    assert res.status_code == 200

    # access token payload에서 user_id 확인
    from rest_framework_simplejwt.tokens import AccessToken

    payload = AccessToken(res.json()["access"])
    # SimpleJWT 는 user_id 클레임을 문자열로 직렬화하므로 int 로 비교한다.
    assert int(payload["user_id"]) == user.id


# ──────────────────────────────────────────────────────────
# Case 3: 유효하지 않은 토큰 → 401
# ──────────────────────────────────────────────────────────
@responses_lib.activate
@pytest.mark.django_db
def test_invalid_token_returns_401(api):
    responses_lib.add(
        responses_lib.GET,
        GOOGLE_TOKENINFO,
        json={"error": "invalid_token"},
        status=400,
    )

    res = api.post("/auth/google/", {"id_token": "bad-token"}, format="json")

    assert res.status_code == 401
    assert "error" in res.json()


# ──────────────────────────────────────────────────────────
# Case 4: id_token 누락 → 400
# ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_missing_id_token_returns_400(api):
    res = api.post("/auth/google/", {}, format="json")
    assert res.status_code == 400


# ──────────────────────────────────────────────────────────
# Case 5: refresh 토큰(body)으로 새 access 발급
# ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_refresh_token_returns_new_access(api):
    user = UserFactory()
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)

    res = api.post("/auth/refresh/", {"refresh": str(refresh)}, format="json")

    assert res.status_code == 200
    assert "access" in res.json()


# ──────────────────────────────────────────────────────────
# Case 6: 로그아웃 → refresh 토큰 블랙리스트 등록
# ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api):
    user = UserFactory()
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    api.force_authenticate(user=user)

    res = api.post("/auth/logout/", {"refresh": str(refresh)}, format="json")

    assert res.status_code == 200
    assert res.json()["message"] == "로그아웃되었습니다."
