import pytest
from rest_framework.test import APIClient

from tests.factories import SeatFactory, ZoneFactory


@pytest.mark.django_db
def test_seats_query_count(django_assert_num_queries):
    z = ZoneFactory(num_seats=20)

    with django_assert_num_queries(2):  # zone select_related(1) + seats values(1)
        res = APIClient().get(f"/api/v1/zones/{z.id}/seats/")

    assert res.status_code == 200
    assert len(res.json()["seats"]) == 20


@pytest.mark.django_db
def test_seats_response_fields():
    z = ZoneFactory(num_seats=3)

    res = APIClient().get(f"/api/v1/zones/{z.id}/seats/")

    assert res.status_code == 200
    seat = res.json()["seats"][0]
    assert "id" in seat
    assert "seat_number" in seat
    assert "seat_status" in seat


@pytest.mark.django_db
def test_seats_excludes_deleted():
    z = ZoneFactory()
    SeatFactory(zone=z, seat_number="A001")
    SeatFactory(zone=z, seat_number="A002", is_deleted=True)

    res = APIClient().get(f"/api/v1/zones/{z.id}/seats/")

    assert res.status_code == 200
    assert len(res.json()["seats"]) == 1


@pytest.mark.django_db
def test_seats_zone_not_found():
    res = APIClient().get("/api/v1/zones/99999/seats/")
    assert res.status_code == 404
