from django.contrib.auth import get_user_model
from django.db import transaction

from apps.tickets.exceptions import ShareCountMismatch
from apps.tickets.models import Purchase, Ticket

User = get_user_model()


@transaction.atomic
def share_tickets(purchase_id: int, owner, emails: list[str]) -> int:
    """
    한 Purchase의 티켓 중 본인 몫 1장을 제외한 나머지를 지정 유저에게 양도한다.

    - select_for_update()로 동시 양도 race를 방지한다.
    - 이메일은 전원 실제 User여야 하며, 수는 (티켓 수 - 1)과 일치해야 한다.
    - 양도 대상 티켓의 user FK를 재할당한다.

    반환: 양도된 티켓 수.
    """
    purchase = Purchase.objects.get(pk=purchase_id, user=owner, is_deleted=False)

    tickets = list(
        Ticket.objects
        .select_for_update()
        .filter(purchase=purchase, is_deleted=False)
        .order_by("id")
    )
    transferable = len(tickets) - 1  # 본인 1장은 유지

    if len(emails) != transferable:
        raise ShareCountMismatch(expected=transferable, given=len(emails))

    if transferable == 0:
        return 0

    recipients = list(User.objects.filter(email__in=emails))
    found_emails = {u.email for u in recipients}
    missing = [e for e in emails if e not in found_emails]
    if missing:
        raise User.DoesNotExist(f"존재하지 않는 이메일: {missing}")

    # 이메일 순서대로 1:1 매핑 (중복 이메일이 있어도 입력 수만큼 처리)
    by_email = {u.email: u for u in recipients}
    to_transfer = tickets[1:]  # 첫 장은 owner 유지
    for ticket, email in zip(to_transfer, emails):
        ticket.user = by_email[email]

    Ticket.objects.bulk_update(to_transfer, ["user"])
    return len(to_transfer)
