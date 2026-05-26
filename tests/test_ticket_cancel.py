"""Phase 11 — 티켓 취소 (DELETE /tickets/<id>/)"""

import pytest

from apps.events.models import Seat, SeatStatus
from apps.tickets.models import Ticket, TicketStatus
from tests.factories import (
    PurchaseFactory,
    SeatFactory,
    TicketFactory,
    UserFactory,
    ZoneFactory,
)


def _booked_ticket(user):
    zone = ZoneFactory()
    seat = SeatFactory(zone=zone, seat_status=SeatStatus.BOOKED)
    purchase = PurchaseFactory(user=user)
    return TicketFactory(
        user=user, seat=seat, purchase=purchase,
        event_time=zone.event_time, ticket_status=TicketStatus.RESERVED,
    )


@pytest.mark.django_db
def test_cancel_releases_seat_and_soft_deletes(authed_client):
    user = UserFactory()
    ticket = _booked_ticket(user)

    res = authed_client(user).delete(f"/api/v1/tickets/{ticket.id}/")

    assert res.status_code == 200
    ticket.refresh_from_db()
    assert ticket.ticket_status == TicketStatus.CANCELED
    assert ticket.is_deleted is True
    assert Seat.objects.get(pk=ticket.seat_id).seat_status == SeatStatus.AVAILABLE


@pytest.mark.django_db
def test_cancel_already_checked_in_is_rejected(authed_client):
    user = UserFactory()
    ticket = _booked_ticket(user)
    Ticket.objects.filter(pk=ticket.id).update(ticket_status=TicketStatus.CHECKED_IN)

    res = authed_client(user).delete(f"/api/v1/tickets/{ticket.id}/")

    assert res.status_code == 409
    assert Seat.objects.get(pk=ticket.seat_id).seat_status == SeatStatus.BOOKED


@pytest.mark.django_db
def test_cancel_other_users_ticket_is_404(authed_client):
    owner = UserFactory()
    other = UserFactory()
    ticket = _booked_ticket(owner)

    res = authed_client(other).delete(f"/api/v1/tickets/{ticket.id}/")

    assert res.status_code == 404
