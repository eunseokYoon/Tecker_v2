import pytest
from rest_framework.test import APIClient

from tests.factories import EventTimeFactory, SeatFactory, UserFactory, ZoneFactory


# ── 카운터 리셋 헬퍼 ─────────────────────────────────────────────────────────

def _reset_counter(counter, labels: dict):
    """테스트 간 카운터 값이 누적되지 않도록 내부 _value 를 직접 리셋한다."""
    counter.labels(**labels)._value.set(0)


# ── /metrics 엔드포인트 노출 확인 ────────────────────────────────────────────

def test_metrics_endpoint_exposes_known_keys():
    client = APIClient()
    res = client.get("/metrics")
    body = res.content.decode()
    for key in [
        "booking_attempts_total",
        "booking_latency_seconds",
        "aws_rekognition_calls_total",
        "cache_hits_total",
        "antispoof_outage_total",
    ]:
        assert key in body, f"{key} not found in /metrics"


# ── BOOKING_ATTEMPTS 카운터 ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_booking_counter_increments_on_success():
    from apps.core.metrics import BOOKING_ATTEMPTS
    from apps.tickets.services.booking import book_seats
    from django.db import transaction

    user = UserFactory()
    event_time = EventTimeFactory()
    zone = ZoneFactory(event_time=event_time)
    seat = SeatFactory(zone=zone)

    _reset_counter(BOOKING_ATTEMPTS, {"result": "success"})
    before = BOOKING_ATTEMPTS.labels(result="success")._value.get()

    with transaction.atomic():
        book_seats(user=user, event_time_id=event_time.id, seat_ids=[seat.id])

    after = BOOKING_ATTEMPTS.labels(result="success")._value.get()
    assert after == before + 1


@pytest.mark.django_db
def test_booking_counter_increments_on_seat_taken():
    from apps.core.metrics import BOOKING_ATTEMPTS
    from apps.tickets.exceptions import SeatsUnavailable
    from apps.tickets.services.booking import book_seats
    from django.db import transaction

    user = UserFactory()
    event_time = EventTimeFactory()
    zone = ZoneFactory(event_time=event_time)
    seat = SeatFactory(zone=zone)

    _reset_counter(BOOKING_ATTEMPTS, {"result": "seat_taken"})
    before = BOOKING_ATTEMPTS.labels(result="seat_taken")._value.get()

    # 먼저 예매해서 좌석을 소진
    with transaction.atomic():
        book_seats(user=user, event_time_id=event_time.id, seat_ids=[seat.id])

    # 같은 좌석 재시도 → seat_taken
    with pytest.raises(SeatsUnavailable):
        with transaction.atomic():
            book_seats(user=user, event_time_id=event_time.id, seat_ids=[seat.id])

    after = BOOKING_ATTEMPTS.labels(result="seat_taken")._value.get()
    assert after == before + 1


# ── BOOKING_LATENCY 히스토그램 ───────────────────────────────────────────────

@pytest.mark.django_db
def test_booking_latency_observed():
    from apps.core.metrics import BOOKING_LATENCY
    from apps.tickets.services.booking import book_seats
    from django.db import transaction

    user = UserFactory()
    event_time = EventTimeFactory()
    zone = ZoneFactory(event_time=event_time)
    seat = SeatFactory(zone=zone)

    before = BOOKING_LATENCY._sum.get()

    with transaction.atomic():
        book_seats(user=user, event_time_id=event_time.id, seat_ids=[seat.id])

    after = BOOKING_LATENCY._sum.get()
    assert after > before


# ── ANTISPOOF_OUTAGE 카운터 ──────────────────────────────────────────────────

def test_antispoof_outage_increments_on_failure(monkeypatch):
    import requests

    from apps.core.metrics import ANTISPOOF_OUTAGE
    from apps.tickets.exceptions import AntiSpoofUnavailable
    from apps.tickets.services import antispoof

    ANTISPOOF_OUTAGE._value.set(0)
    before = ANTISPOOF_OUTAGE._value.get()

    def _fail(*args, **kwargs):
        raise requests.RequestException("connection refused")

    # tenacity retry 를 우회하여 단일 호출로 테스트
    monkeypatch.setattr(requests, "post", _fail)
    monkeypatch.setattr(
        antispoof.is_real_face, "retry",
        antispoof.is_real_face.retry.copy(stop=antispoof.stop_after_attempt(1)),
        raising=False,
    )

    with pytest.raises(AntiSpoofUnavailable):
        antispoof.is_real_face("stub-b64")

    after = ANTISPOOF_OUTAGE._value.get()
    assert after > before
