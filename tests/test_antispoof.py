"""
Phase 6 — 안티스푸핑 retry 단위 테스트

핵심 검증
- HTTP 500 응답 시 tenacity가 정확히 3회 재시도하는가
- 서버가 real 을 반환하면 True 를 반환하는가
- 서버가 fake 를 반환하면 False 를 반환하는가
"""

import pytest
import responses as resp_lib

from apps.tickets.exceptions import AntiSpoofUnavailable
from apps.tickets.services.antispoof import is_real_face


ANTISPOOF_URL = "http://antispoof:5001/predict"


@pytest.fixture(autouse=True)
def _reset_tenacity():
    """tenacity 내부 상태(retry statistics)를 각 테스트 전에 초기화한다."""
    is_real_face.retry.statistics.clear()
    yield


@resp_lib.activate
def test_antispoof_retries_three_times_on_server_error(settings):
    """
    서버가 500 을 3번 반환하면 tenacity 가 3회 시도 후 AntiSpoofUnavailable 을 발생시켜야 한다.
    """
    settings.AI_SERVER_URL = "http://antispoof:5001"

    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={}, status=500)
    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={}, status=500)
    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={}, status=500)

    with pytest.raises(AntiSpoofUnavailable):
        is_real_face("base64string")

    assert len(resp_lib.calls) == 3, f"기대: 3회, 실제: {len(resp_lib.calls)}회"


@resp_lib.activate
def test_antispoof_returns_true_on_real(settings):
    """서버가 label=real 을 반환하면 True 이어야 한다."""
    settings.AI_SERVER_URL = "http://antispoof:5001"

    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={"label": "real"}, status=200)

    result = is_real_face("base64string")
    assert result is True


@resp_lib.activate
def test_antispoof_returns_false_on_fake(settings):
    """서버가 label=fake 를 반환하면 False 이어야 한다."""
    settings.AI_SERVER_URL = "http://antispoof:5001"

    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={"label": "fake"}, status=200)

    result = is_real_face("base64string")
    assert result is False


@resp_lib.activate
def test_antispoof_retries_then_succeeds(settings):
    """첫 번째 실패 후 두 번째 시도에서 성공하면 True 를 반환해야 한다."""
    settings.AI_SERVER_URL = "http://antispoof:5001"

    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={}, status=500)
    resp_lib.add(resp_lib.POST, ANTISPOOF_URL, json={"label": "real"}, status=200)

    result = is_real_face("base64string")
    assert result is True
    assert len(resp_lib.calls) == 2
