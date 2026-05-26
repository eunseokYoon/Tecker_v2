"""
동시성 회귀 테스트.

transaction=True: pytest-django가 테스트마다 실제 트랜잭션 커밋/롤백을 허용.
→ select_for_update()의 행 잠금이 실제로 동작하는지 검증할 수 있다.
→ Docker MySQL 환경에서만 정확한 동시성 보장 확인 가능.
"""
import threading

import pytest
from django.db import close_old_connections, connection, transaction

from apps.events.models import SeatStatus
from apps.tickets.exceptions import SeatsUnavailable
from apps.tickets.services.booking import book_seats
from tests.factories import SeatFactory, UserFactory, ZoneFactory


@pytest.mark.django_db(transaction=True)
def test_no_double_booking_under_concurrent_requests():
    zone = ZoneFactory()
    seat = SeatFactory(zone=zone, seat_status=SeatStatus.AVAILABLE)
    users = [UserFactory() for _ in range(10)]
    results = []
    lock = threading.Lock()

    def attempt(user):
        close_old_connections()  # 스레드별 신규 DB 커넥션 보장
        try:
            with transaction.atomic():
                book_seats(user, seat.zone.event_time_id, [seat.id])
            with lock:
                results.append("success")
        except SeatsUnavailable:
            with lock:
                results.append("blocked")
        finally:
            connection.close()  # 스레드 커넥션 반환

    threads = [threading.Thread(target=attempt, args=(u,)) for u in users]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 10명 중 정확히 1명만 성공, 나머지 9명은 차단
    assert results.count("success") == 1
    assert results.count("blocked") == 9

    seat.refresh_from_db()
    assert seat.seat_status == SeatStatus.BOOKED


@pytest.mark.django_db(transaction=True)
def test_view_count_increments_atomically():
    """view_count F() 업데이트가 동시 100 요청에서 누락 없이 정확히 증가하는지 확인."""
    from apps.events.models import Event
    from tests.factories import EventFactory

    e = EventFactory(view_count=0)
    event_id = e.id

    def increment():
        close_old_connections()
        try:
            Event.objects.filter(pk=event_id).update(
                view_count=__import__("django.db.models", fromlist=["F"]).F("view_count") + 1
            )
        finally:
            connection.close()

    threads = [threading.Thread(target=increment) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    e.refresh_from_db()
    assert e.view_count == 100
