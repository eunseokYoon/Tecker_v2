import time

from django.db import transaction

from apps.core.metrics import BOOKING_ATTEMPTS, BOOKING_LATENCY
from apps.events.models import Seat, SeatStatus
from apps.tickets.exceptions import AlreadyPaid, SeatsUnavailable
from apps.tickets.models import Purchase, PurchaseStatus, Ticket, TicketStatus


def book_seats(user, event_time_id: int, seat_ids: list[int]) -> tuple:
    """
    행 잠금(select_for_update)으로 좌석을 원자적으로 예매한다.

    - 호출자가 transaction.atomic()으로 감싸야 select_for_update가 동작한다.
    - 좌석 수 불일치(이미 예매 or 삭제)이면 SeatsUnavailable을 발생시킨다.
    - on_commit Celery 스케줄링은 호출자(View)에서 처리한다.
    """
    start = time.perf_counter()
    try:
        seats = list(
            Seat.objects
            .select_for_update()
            .select_related("zone")
            .filter(
                id__in=seat_ids,
                seat_status=SeatStatus.AVAILABLE,
                is_deleted=False,
            )
        )
        if len(seats) != len(seat_ids):
            BOOKING_ATTEMPTS.labels(result="seat_taken").inc()
            raise SeatsUnavailable(seat_ids=seat_ids)

        total_price = sum(s.zone.price for s in seats)

        purchase = Purchase.objects.create(
            user=user,
            purchase_status=PurchaseStatus.PENDING,
            total_price=total_price,
        )
        tickets = Ticket.objects.bulk_create([
            Ticket(
                user=user,
                seat=s,
                purchase=purchase,
                event_time_id=event_time_id,
                ticket_status=TicketStatus.BOOKED,
            )
            for s in seats
        ])
        Seat.objects.filter(id__in=seat_ids).update(seat_status=SeatStatus.BOOKED)

        BOOKING_ATTEMPTS.labels(result="success").inc()
        return purchase, [t.id for t in tickets]

    except SeatsUnavailable:
        raise
    except Exception:
        BOOKING_ATTEMPTS.labels(result="exception").inc()
        raise
    finally:
        BOOKING_LATENCY.observe(time.perf_counter() - start)


@transaction.atomic
def pay_purchase(purchase_id: int, user) -> list[int]:
    """
    결제 완료 처리.

    - select_for_update()로 중복 결제 race를 막는다.
    - tickets 상태를 루프 없이 bulk update → N+1 없음.
    """
    purchase = Purchase.objects.select_for_update().get(
        id=purchase_id,
        user=user,
        is_deleted=False,
    )
    if purchase.purchase_status != PurchaseStatus.PENDING:
        raise AlreadyPaid()

    purchase.purchase_status = PurchaseStatus.COMPLETED
    purchase.save(update_fields=["purchase_status", "updated_at"])

    ticket_ids = list(
        Ticket.objects
        .filter(purchase=purchase)
        .values_list("id", flat=True)
    )
    Ticket.objects.filter(id__in=ticket_ids).update(
        ticket_status=TicketStatus.RESERVED,
    )
    return ticket_ids
