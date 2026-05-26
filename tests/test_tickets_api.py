import pytest
from rest_framework.test import APIClient

from tests.factories import (
    EventTimeFactory,
    PurchaseFactory,
    SeatFactory,
    TicketFactory,
    UserFactory,
    ZoneFactory,
)


def _make_ticket(user):
    """테스트용 완전한 티켓 트리 생성 헬퍼."""
    zone = ZoneFactory()  # ZoneFactory → EventTimeFactory → EventFactory 자동 생성
    seat = SeatFactory(zone=zone)
    purchase = PurchaseFactory(user=user)
    return TicketFactory(
        user=user,
        seat=seat,
        purchase=purchase,
        event_time=zone.event_time,
    )


# ──────────────────────────────────────────────────────────
# 쿼리 수 회귀 테스트 (핵심)
# ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTicketListAPI:
    def test_query_count_is_constant_regardless_of_size(
        self, authed_client, django_assert_num_queries
    ):
        user = UserFactory()
        for _ in range(30):
            _make_ticket(user)
        client = authed_client(user)

        with django_assert_num_queries(2):  # COUNT(1) + SELECT JOIN(1)
            res = client.get("/api/v1/tickets/?page=1&limit=30")

        assert res.status_code == 200
        assert len(res.json()["results"]) == 30

    def test_detail_query_count(self, authed_client, django_assert_num_queries):
        user = UserFactory()
        ticket = _make_ticket(user)
        client = authed_client(user)

        with django_assert_num_queries(1):  # SELECT JOIN 단 1회
            res = client.get(f"/api/v1/tickets/{ticket.id}/")

        assert res.status_code == 200

    # ──────────────────────────────────────────────────────────
    # 응답 필드 검증
    # ──────────────────────────────────────────────────────────

    def test_list_response_fields(self, authed_client):
        user = UserFactory()
        _make_ticket(user)
        res = authed_client(user).get("/api/v1/tickets/")

        assert res.status_code == 200
        ticket_data = res.json()["results"][0]
        assert "id" in ticket_data
        assert "event_name" in ticket_data
        assert "event_date" in ticket_data
        assert "event_location" in ticket_data
        assert "zone_name" in ticket_data
        assert "zone_rank" in ticket_data
        assert "seat_number" in ticket_data
        assert "ticket_status" in ticket_data
        assert "purchase_id" in ticket_data

    def test_detail_response_fields(self, authed_client):
        user = UserFactory()
        ticket = _make_ticket(user)
        res = authed_client(user).get(f"/api/v1/tickets/{ticket.id}/")

        assert res.status_code == 200
        data = res.json()
        # 상세에만 있는 필드
        assert "artist" in data
        assert "genre" in data
        assert "zone_price" in data
        assert "purchase_status" in data

    # ──────────────────────────────────────────────────────────
    # 인증 / 격리 테스트
    # ──────────────────────────────────────────────────────────

    def test_list_requires_authentication(self):
        res = APIClient().get("/api/v1/tickets/")
        assert res.status_code == 401

    def test_list_returns_only_own_tickets(self, authed_client):
        user_a = UserFactory()
        user_b = UserFactory()
        _make_ticket(user_a)
        _make_ticket(user_b)

        res = authed_client(user_a).get("/api/v1/tickets/")

        assert res.status_code == 200
        assert res.json()["count"] == 1

    def test_detail_returns_404_for_other_users_ticket(self, authed_client):
        owner = UserFactory()
        other = UserFactory()
        ticket = _make_ticket(owner)

        res = authed_client(other).get(f"/api/v1/tickets/{ticket.id}/")

        assert res.status_code == 404

    # ──────────────────────────────────────────────────────────
    # 페이지네이션
    # ──────────────────────────────────────────────────────────

    def test_pagination_limit(self, authed_client):
        user = UserFactory()
        for _ in range(5):
            _make_ticket(user)

        res = authed_client(user).get("/api/v1/tickets/?limit=3")

        assert res.status_code == 200
        body = res.json()
        assert len(body["results"]) == 3
        assert body["count"] == 5
        assert body["next"] is not None

    def test_empty_list(self, authed_client):
        user = UserFactory()
        res = authed_client(user).get("/api/v1/tickets/")

        assert res.status_code == 200
        assert res.json()["results"] == []
        assert res.json()["count"] == 0
