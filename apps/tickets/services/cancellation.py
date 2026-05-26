from django.db import transaction

from apps.events.models import Seat, SeatStatus
from apps.tickets.exceptions import TicketNotCancelable
from apps.tickets.models import Ticket, TicketStatus

# 취소 불가능한 종료 상태
_NON_CANCELABLE = {TicketStatus.CHECKED_IN, TicketStatus.CANCELED}


@transaction.atomic
def cancel_ticket(ticket: Ticket) -> dict:
    """
    티켓을 취소하고 좌석을 다시 예매 가능 상태로 되돌린다.

    - select_for_update()로 동시 취소/결제 race를 방지한다.
    - 이미 입장(checked_in)했거나 취소된 티켓이면 TicketNotCancelable.
    - 좌석 status → available, 티켓 status → canceled, is_deleted → True (소프트 삭제).
    """
    locked = Ticket.objects.select_for_update().get(pk=ticket.pk)

    if locked.ticket_status in _NON_CANCELABLE:
        raise TicketNotCancelable(ticket_id=locked.pk, ticket_status=locked.ticket_status)

    locked.ticket_status = TicketStatus.CANCELED
    locked.is_deleted = True
    locked.save(update_fields=["ticket_status", "is_deleted", "updated_at"])

    Seat.objects.filter(pk=locked.seat_id).update(seat_status=SeatStatus.AVAILABLE)

    return {
        "ticket_id": locked.pk,
        "seat_id": locked.seat_id,
        "ticket_status": locked.ticket_status,
        "is_deleted": locked.is_deleted,
        "seat_status": SeatStatus.AVAILABLE,
    }
