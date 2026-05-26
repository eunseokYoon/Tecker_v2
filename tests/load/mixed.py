"""
Phase 10 — 혼합 부하 시나리오 (Locust)

실행:
  locust -f tests/load/mixed.py --headless \\
         --users 100 --spawn-rate 10 -t 60s \\
         --host http://localhost:8000 \\
         --csv=locust_report --html=locust_report.html

환경변수:
  LOCUST_TOKEN  — Bearer 토큰 (미설정 시 인증 필요 엔드포인트 skip)
"""

import os
import random

from locust import HttpUser, between, task

_TOKEN = os.getenv("LOCUST_TOKEN", "")
_AUTH = {"Authorization": f"Bearer {_TOKEN}"} if _TOKEN else {}

# 부하 테스트용 seed 데이터 ID 범위
_EVENT_IDS = list(range(1, 11))
_EVENT_TIME_IDS = list(range(1, 21))  # 10 events × 2 event_times each
_SEAT_IDS = list(range(1, 3241))  # 10 events × 2 times × 162 seats


class ReadOnlyUser(HttpUser):
    """캐시 히트율 측정 — 인증 불필요."""

    wait_time = between(0.2, 1)
    weight = 6  # 전체 VU 중 60%

    @task(5)
    def event_list(self):
        self.client.get("/api/v1/events/view/", name="GET /events/view/")

    @task(3)
    def event_list_page2(self):
        with self.client.get(
            "/api/v1/events/view/?page=2",
            name="GET /events/view/?page=2",
            catch_response=True,
        ) as res:
            if res.status_code in (200, 404):
                res.success()
            else:
                res.failure(f"Unexpected {res.status_code}")

    @task(2)
    def event_detail(self):
        eid = random.choice(_EVENT_IDS)
        self.client.get(f"/api/v1/events/view/{eid}/", name="GET /events/view/{id}/")

    @task(1)
    def healthz(self):
        self.client.get("/healthz", name="GET /healthz")


class BookingUser(HttpUser):
    """예매 + 결제 흐름 — Bearer 토큰 필요."""

    wait_time = between(1, 3)
    weight = 4  # 전체 VU 중 40%

    def on_start(self):
        self._purchase_id: int | None = None

    @task(3)
    def book_seat(self):
        if not _TOKEN:
            return
        event_id = random.choice(_EVENT_IDS)
        event_time_id = random.choice(_EVENT_TIME_IDS)
        seat_id = random.choice(_SEAT_IDS)
        with self.client.post(
            f"/api/v1/events/view/{event_id}/tickets/buy",
            json={"event_time_id": event_time_id, "seat_id": [seat_id]},
            headers=_AUTH,
            name="POST /buy",
            catch_response=True,
        ) as res:
            if res.status_code == 201:
                data = res.json()
                self._purchase_id = data.get("purchase_id")
                res.success()
            elif res.status_code in (400, 409):
                # 좌석 취소·중복 → 정상 시나리오
                res.success()
            else:
                res.failure(f"Unexpected {res.status_code}")

    @task(1)
    def pay(self):
        if not _TOKEN or not self._purchase_id:
            return
        with self.client.patch(
            f"/api/v1/events/view/{self._purchase_id}/tickets/pay/",
            headers=_AUTH,
            name="PATCH /pay",
            catch_response=True,
        ) as res:
            if res.status_code in (200, 409):
                res.success()
            else:
                res.failure(f"Unexpected {res.status_code}")
            self._purchase_id = None
