"""Phase 11 — 티켓 입장 처리 (PATCH /tickets/<id>/certification/)"""

import pytest

from apps.tickets.models import Ticket, TicketStatus
from tests.factories import TicketFactory, UserFactory


@pytest.mark.django_db
def test_certification_marks_checked_in(authed_client):
    user = UserFactory()
    ticket = TicketFactory(user=user, ticket_status=TicketStatus.VERIFIED)

    res = authed_client(user).patch(f"/api/v1/tickets/{ticket.id}/certification/")

    assert res.status_code == 200
    ticket.refresh_from_db()
    assert ticket.ticket_status == TicketStatus.CHECKED_IN
    assert ticket.checked_in_at is not None


@pytest.mark.django_db
def test_certification_twice_returns_400(authed_client):
    user = UserFactory()
    ticket = TicketFactory(user=user, ticket_status=TicketStatus.CHECKED_IN)

    res = authed_client(user).patch(f"/api/v1/tickets/{ticket.id}/certification/")

    assert res.status_code == 400


@pytest.mark.django_db
def test_certification_other_users_ticket_is_404(authed_client):
    owner = UserFactory()
    other = UserFactory()
    ticket = TicketFactory(user=owner, ticket_status=TicketStatus.VERIFIED)

    res = authed_client(other).patch(f"/api/v1/tickets/{ticket.id}/certification/")

    assert res.status_code == 404
    assert Ticket.objects.get(pk=ticket.id).ticket_status == TicketStatus.VERIFIED
