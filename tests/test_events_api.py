import pytest
from rest_framework.test import APIClient

from tests.factories import EventFactory


@pytest.mark.django_db
class TestEventListAPI:
    def test_query_count_is_constant(self, django_assert_num_queries):
        for _ in range(10):
            EventFactory.create_with_full_tree(num_times=2, num_zones=2, num_seats=5)

        client = APIClient()
        with django_assert_num_queries(2):  # 1 COUNT + 1 SELECT (둘 다 annotate 포함)
            res = client.get("/api/v1/events/?page=1&limit=10")

        assert res.status_code == 200
        assert len(res.json()["events"]) == 10
        assert res.json()["totalCount"] == 10

    def test_search_keyword_filters_results(self):
        EventFactory(name="아이유 콘서트")
        EventFactory(name="BTS 월드투어")

        res = APIClient().get("/api/v1/events/?keyword=아이유")

        assert res.status_code == 200
        assert res.json()["totalCount"] == 1
        assert res.json()["events"][0]["name"] == "아이유 콘서트"

    def test_search_artist_filters_results(self):
        EventFactory(name="서울 콘서트", artist="아이유")
        EventFactory(name="부산 공연", artist="BTS")

        res = APIClient().get("/api/v1/events/?keyword=아이유")

        assert res.status_code == 200
        assert res.json()["totalCount"] == 1

    def test_category_filter(self):
        EventFactory(genre="concert")
        EventFactory(genre="musical")
        EventFactory(genre="musical")

        res = APIClient().get("/api/v1/events/?category=musical")

        assert res.status_code == 200
        assert res.json()["totalCount"] == 2

    def test_sort_popular(self):
        EventFactory(name="인기없음", view_count=10)
        EventFactory(name="인기있음", view_count=999)

        res = APIClient().get("/api/v1/events/?sort=popular")

        assert res.status_code == 200
        assert res.json()["events"][0]["name"] == "인기있음"

    def test_event_list_response_fields(self):
        EventFactory.create_with_full_tree(num_times=1, num_zones=1, num_seats=1)

        res = APIClient().get("/api/v1/events/")

        assert res.status_code == 200
        event = res.json()["events"][0]
        assert "id" in event
        assert "name" in event
        assert "artist" in event
        assert "genre" in event
        assert "location" in event
        assert "view_count" in event
        assert "min_price" in event
        assert "next_date" in event

    def test_pagination_limit(self):
        for _ in range(15):
            EventFactory()

        res = APIClient().get("/api/v1/events/?limit=5")

        assert res.status_code == 200
        assert len(res.json()["events"]) == 5
        assert res.json()["totalCount"] == 15

    def test_empty_list(self):
        res = APIClient().get("/api/v1/events/")

        assert res.status_code == 200
        assert res.json()["events"] == []
        assert res.json()["totalCount"] == 0
