"""Phase 11 — 티켓 QR 코드 (GET /tickets/<id>/qr/)"""

import base64

import pytest

from tests.factories import TicketFactory, UserFactory


@pytest.mark.django_db
def test_qr_returns_base64_png(authed_client):
    user = UserFactory()
    ticket = TicketFactory(user=user)

    res = authed_client(user).get(f"/api/v1/tickets/{ticket.id}/qr/")

    assert res.status_code == 200
    qr_b64 = res.json()["qr_base64"]
    decoded = base64.b64decode(qr_b64)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"  # PNG 매직 넘버


@pytest.mark.django_db
def test_qr_other_users_ticket_is_404(authed_client):
    owner = UserFactory()
    other = UserFactory()
    ticket = TicketFactory(user=owner)

    res = authed_client(other).get(f"/api/v1/tickets/{ticket.id}/qr/")

    assert res.status_code == 404
