"""Phase 11 — 티켓 공유/양도 (POST /tickets/<purchase_id>/share/)"""

import pytest

from apps.tickets.models import Ticket
from tests.factories import PurchaseFactory, TicketFactory, UserFactory


def _purchase_with_tickets(owner, count):
    purchase = PurchaseFactory(user=owner)
    TicketFactory.create_batch(count, user=owner, purchase=purchase)
    return purchase


@pytest.mark.django_db
def test_share_transfers_tickets_to_recipients(authed_client):
    owner = UserFactory()
    r1 = UserFactory(email="r1@test.io")
    r2 = UserFactory(email="r2@test.io")
    purchase = _purchase_with_tickets(owner, count=3)  # 양도 가능 2장

    res = authed_client(owner).post(
        f"/api/v1/tickets/{purchase.id}/share/",
        {"ticket_user_emails": ["r1@test.io", "r2@test.io"]},
        format="json",
    )

    assert res.status_code == 200
    owners = set(
        Ticket.objects.filter(purchase=purchase).values_list("user_id", flat=True)
    )
    assert owners == {owner.id, r1.id, r2.id}


@pytest.mark.django_db
def test_share_count_mismatch_returns_400(authed_client):
    owner = UserFactory()
    UserFactory(email="r1@test.io")
    purchase = _purchase_with_tickets(owner, count=3)  # 양도 가능 2장인데 1명만 지정

    res = authed_client(owner).post(
        f"/api/v1/tickets/{purchase.id}/share/",
        {"ticket_user_emails": ["r1@test.io"]},
        format="json",
    )

    assert res.status_code == 400


@pytest.mark.django_db
def test_share_nonexistent_email_returns_400_and_rolls_back(authed_client):
    owner = UserFactory()
    UserFactory(email="r1@test.io")
    purchase = _purchase_with_tickets(owner, count=3)

    res = authed_client(owner).post(
        f"/api/v1/tickets/{purchase.id}/share/",
        {"ticket_user_emails": ["r1@test.io", "ghost@test.io"]},
        format="json",
    )

    assert res.status_code == 400
    # atomic 롤백: 모든 티켓이 여전히 owner 소유
    owners = set(
        Ticket.objects.filter(purchase=purchase).values_list("user_id", flat=True)
    )
    assert owners == {owner.id}


@pytest.mark.django_db
def test_share_other_users_purchase_is_404(authed_client):
    owner = UserFactory()
    other = UserFactory()
    UserFactory(email="r1@test.io")
    purchase = _purchase_with_tickets(owner, count=2)

    res = authed_client(other).post(
        f"/api/v1/tickets/{purchase.id}/share/",
        {"ticket_user_emails": ["r1@test.io"]},
        format="json",
    )

    assert res.status_code == 404
