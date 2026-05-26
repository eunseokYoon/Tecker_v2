import pytest
from rest_framework.test import APIClient

from tests.factories import EventFactory


@pytest.mark.django_db
def test_detail_query_count(django_assert_num_queries):
    e = EventFactory.create_with_full_tree(num_times=5, num_zones=3, num_seats=10)

    with django_assert_num_queries(5):
        # event(1) + event_times prefetch(1) + zones prefetch(1) + aggregate(1) + view_count update(1)
        res = APIClient().get(f"/api/v1/events/{e.id}/")

    assert res.status_code == 200


@pytest.mark.django_db
def test_detail_response_fields():
    e = EventFactory.create_with_full_tree(num_times=2, num_zones=2, num_seats=5)

    res = APIClient().get(f"/api/v1/events/{e.id}/")

    assert res.status_code == 200
    data = res.json()

    assert data["id"] == e.id
    assert data["name"] == e.name
    assert "event_times" in data
    assert len(data["event_times"]) == 2
    assert "zones" in data["event_times"][0]
    assert len(data["event_times"][0]["zones"]) == 2
    assert "price_range" in data
    assert data["price_range"]["min"] is not None
    assert data["price_range"]["max"] is not None


@pytest.mark.django_db
def test_detail_view_count_increments():
    e = EventFactory(view_count=0)

    APIClient().get(f"/api/v1/events/{e.id}/")

    e.refresh_from_db()
    assert e.view_count == 1


@pytest.mark.django_db
def test_detail_not_found():
    res = APIClient().get("/api/v1/events/99999/")
    assert res.status_code == 404
