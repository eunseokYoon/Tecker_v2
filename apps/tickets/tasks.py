import logging

from celery import shared_task
from django.db import transaction

from apps.events.models import Seat, SeatStatus
from apps.tickets.models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_cancel_ticket(self, ticket_id: int) -> None:
    """
    예매 후 300초(5분) 이내에 결제가 완료되지 않으면 좌석을 자동 취소한다.

    - select_for_update()로 동시 취소/결제 race를 방지한다.
    - BOOKED 상태가 아니면 멱등 처리(이미 결제됐거나 취소됨).
    """
    try:
        with transaction.atomic():
            try:
                ticket = Ticket.objects.select_for_update().get(
                    pk=ticket_id, is_deleted=False
                )
            except Ticket.DoesNotExist:
                logger.warning("auto_cancel_ticket: ticket %s not found", ticket_id)
                return

            if ticket.ticket_status != TicketStatus.BOOKED:
                logger.info(
                    "auto_cancel_ticket: ticket %s already %s, skip",
                    ticket_id,
                    ticket.ticket_status,
                )
                return

            ticket.ticket_status = TicketStatus.CANCELED
            ticket.save(update_fields=["ticket_status", "updated_at"])

            Seat.objects.filter(pk=ticket.seat_id).update(
                seat_status=SeatStatus.AVAILABLE
            )
            logger.info("auto_cancel_ticket: ticket %s canceled, seat released", ticket_id)

    except Exception as exc:
        logger.error("auto_cancel_ticket: error for ticket %s: %s", ticket_id, exc)
        raise self.retry(exc=exc)
