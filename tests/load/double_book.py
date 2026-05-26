"""
Locust 부하 시나리오: 같은 좌석에 대한 동시 예매 경쟁 테스트.

실행:
    locust -f tests/load/double_book.py --headless \\
           --users 100 --spawn-rate 100 -t 30s \\
           --host http://localhost:8000 \\
           --token <ACCESS_TOKEN> --event-id 1 --event-time-id 1 --seat-id 42

검증 (테스트 종료 후 DB 직접 확인):
    SELECT COUNT(*) FROM ticket WHERE seat_id=42 AND ticket_status='booked';
    -- 결과: 1 (목표)
"""
from locust import HttpUser, between, events, task


@events.init_command_line_parser.add_listener
def add_arguments(parser):
    parser.add_argument("--token", type=str, default="", help="Bearer access token")
    parser.add_argument("--event-id", type=int, default=1, help="Event ID")
    parser.add_argument("--event-time-id", type=int, default=1, help="EventTime ID")
    parser.add_argument("--seat-id", type=int, default=42, help="Seat ID to contend on")


class BookingUser(HttpUser):
    wait_time = between(0.05, 0.2)  # 빠른 동시 요청 시뮬레이션

    def on_start(self):
        opts = self.environment.parsed_options
        self.token = opts.token
        self.event_id = opts.event_id
        self.event_time_id = opts.event_time_id
        self.seat_id = opts.seat_id

    @task
    def book_same_seat(self):
        self.client.post(
            f"/api/v1/events/{self.event_id}/tickets/buy",
            json={
                "event_time_id": self.event_time_id,
                "seat_ids": [self.seat_id],
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="POST /buy [contended]",
        )
