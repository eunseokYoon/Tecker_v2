import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.tickets.exceptions import AlreadyPaid
from apps.tickets.models import PurchaseStatus, TicketStatus
from apps.tickets.services.booking import pay_purchase
from tests.factories import (
    EventTimeFactory,
    PurchaseFactory,
    SeatFactory,
    TicketFactory,
    UserFactory,
    ZoneFactory,
)


# ──────────────────────────────────────────────────────────
# pay_purchase 서비스 유닛 테스트 (HTTP 오버헤드 없이 쿼리 수 정밀 측정)
# ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_pay_purchase_query_count():
    user = UserFactory()
    purchase = PurchaseFactory(user=user, purchase_status=PurchaseStatus.PENDING)
    event_time = EventTimeFactory()
    zone = ZoneFactory(event_time=event_time)
    seats = [SeatFactory(zone=zone) for _ in range(5)]
    for seat in seats:
        TicketFactory(
            user=user,
            purchase=purchase,
            event_time=event_time,
            seat=seat,
            ticket_status=TicketStatus.BOOKED,
        )

    with CaptureQueriesContext(connection) as ctx:
        pay_purchase(purchase_id=purchase.id, user=user)

    # SAVEPOINT/RELEASE 는 테스트 트랜잭션 안에서 @transaction.atomic 이
    # 만들어내는 하네스 아티팩트이므로 제외하고 실제 쿼리만 센다.
    real_queries = [
        q for q in ctx.captured_queries
        if not q["sql"].startswith(("SAVEPOINT", "RELEASE"))
    ]
    # select_for_update get(1) + save(1) + values_list(1) + bulk update(1)
    assert len(real_queries) == 4


@pytest.mark.django_db
def test_pay_purchase_changes_status():
    user = UserFactory()
    purchase = PurchaseFactory(user=user, purchase_status=PurchaseStatus.PENDING)

    pay_purchase(purchase_id=purchase.id, user=user)

    purchase.refresh_from_db()
    assert purchase.purchase_status == PurchaseStatus.COMPLETED


@pytest.mark.django_db
def test_pay_purchase_updates_ticket_status():
    user = UserFactory()
    purchase = PurchaseFactory(user=user, purchase_status=PurchaseStatus.PENDING)
    event_time = EventTimeFactory()
    zone = ZoneFactory(event_time=event_time)
    seat = SeatFactory(zone=zone)
    ticket = TicketFactory(
        user=user,
        purchase=purchase,
        event_time=event_time,
        seat=seat,
        ticket_status=TicketStatus.BOOKED,
    )

    pay_purchase(purchase_id=purchase.id, user=user)

    ticket.refresh_from_db()
    assert ticket.ticket_status == TicketStatus.RESERVED


@pytest.mark.django_db
def test_pay_purchase_raises_already_paid():
    user = UserFactory()
    purchase = PurchaseFactory(user=user, purchase_status=PurchaseStatus.COMPLETED)

    with pytest.raises(AlreadyPaid):
        pay_purchase(purchase_id=purchase.id, user=user)


# ──────────────────────────────────────────────────────────
# PATCH /api/v1/purchases/<id>/pay/ HTTP 통합 테스트
# ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_pay_view_returns_200():
    user = UserFactory()
    purchase = PurchaseFactory(user=user, purchase_status=PurchaseStatus.PENDING)
    event_time = EventTimeFactory()
    zone = ZoneFactory(event_time=event_time)
    seat = SeatFactory(zone=zone)
    TicketFactory(
        user=user,
        purchase=purchase,
        event_time=event_time,
        seat=seat,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    res = client.patch(f"/api/v1/purchases/{purchase.id}/pay/", format="json")

    assert res.status_code == 200
    assert "ticket_ids" in res.json()


@pytest.mark.django_db
def test_pay_view_requires_authentication():
    purchase = PurchaseFactory()

    res = APIClient().patch(f"/api/v1/purchases/{purchase.id}/pay/", format="json")

    assert res.status_code == 401


@pytest.mark.django_db
def test_pay_view_already_paid_returns_409():
    user = UserFactory()
    purchase = PurchaseFactory(user=user, purchase_status=PurchaseStatus.COMPLETED)

    client = APIClient()
    client.force_authenticate(user=user)

    res = client.patch(f"/api/v1/purchases/{purchase.id}/pay/", format="json")

    assert res.status_code == 409


@pytest.mark.django_db
def test_pay_view_other_user_returns_404():
    owner = UserFactory()
    other = UserFactory()
    purchase = PurchaseFactory(user=owner, purchase_status=PurchaseStatus.PENDING)

    client = APIClient()
    client.force_authenticate(user=other)

    res = client.patch(f"/api/v1/purchases/{purchase.id}/pay/", format="json")

    assert res.status_code == 404
