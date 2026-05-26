"""
Phase 7 — 이벤트 캐시 단위 테스트

핵심 검증
- 동일 요청 2회째에 DB 쿼리가 0인가  (cache hit)
- Event/EventTime 변경 시 캐시가 무효화되는가
- 캐시 hit 카운터가 증가하는가
"""

import pytest
from django.core.cache import cache
from django.test.utils import override_settings

from tests.factories import EventFactory, EventTimeFactory

# 테스트에서는 in-memory 캐시 사용 (Redis 미필요)
LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_second_request_is_cache_hit(api_client, django_assert_num_queries):
    """
    동일한 파라미터로 2번째 요청 시 DB 쿼리가 0이어야 한다.
    """
    EventFactory.create_batch(3)
    cache.clear()

    api_client.get("/api/v1/events/?page=1")  # cache miss — DB hit

    with django_assert_num_queries(0):
        api_client.get("/api/v1/events/?page=1")  # cache hit — DB 0 쿼리


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_different_params_are_different_cache_keys(api_client, django_assert_num_queries):
    """
    파라미터가 다르면 별도 캐시 키를 사용해야 한다.
    """
    EventFactory(name="rock concert", genre="concert")
    cache.clear()

    api_client.get("/api/v1/events/?page=1")
    api_client.get("/api/v1/events/?page=2")  # 다른 키 → 반드시 DB 쿼리

    # page=1 은 이미 캐시됨 → DB 0
    with django_assert_num_queries(0):
        api_client.get("/api/v1/events/?page=1")


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_event_save_invalidates_cache(api_client):
    """
    Event 저장 시그널이 발생하면 캐시가 무효화되어 새 데이터가 응답에 포함되어야 한다.
    """
    e = EventFactory(name="old name")
    cache.clear()

    api_client.get("/api/v1/events/?page=1")  # 캐시 적재

    e.name = "new name"
    e.save()  # post_save 시그널 → _invalidate_events → cache.clear()

    res = api_client.get("/api/v1/events/?page=1")
    assert "new name" in res.content.decode(), "캐시 무효화 후 새 이름이 보여야 합니다."


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_event_delete_invalidates_cache(api_client):
    """
    Event 삭제(soft-delete) 시 캐시가 무효화되어야 한다.
    """
    e = EventFactory()
    cache.clear()

    first = api_client.get("/api/v1/events/?page=1")
    initial_count = first.json()["totalCount"]

    e.soft_delete()  # post_save 발생 → 무효화

    second = api_client.get("/api/v1/events/?page=1")
    assert second.json()["totalCount"] == initial_count - 1


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_event_detail_cached(api_client, django_assert_num_queries):
    """
    상세 조회 2회째는 DB SELECT 쿼리가 없어야 한다.
    (view_count UPDATE는 여전히 발생하므로 1 쿼리는 허용)
    """
    e = EventFactory()
    cache.clear()

    api_client.get(f"/api/v1/events/{e.id}/")  # miss

    # 2회째: SELECT 없이 view_count UPDATE(1) 만 발생
    with django_assert_num_queries(1):
        api_client.get(f"/api/v1/events/{e.id}/")
