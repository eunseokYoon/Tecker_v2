from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedSoftDelete
from apps.events.models import EventTime, Seat


class PurchaseStatus(models.TextChoices):
    PENDING = "pending", "결제 전"
    COMPLETED = "completed", "결제 완료"
    CANCELED = "canceled", "취소"


class TicketStatus(models.TextChoices):
    BOOKED = "booked", "예매됨"
    RESERVED = "reserved", "결제완료"
    VERIFIED = "verified", "얼굴등록완료"
    CHECKED_IN = "checked_in", "입장완료"
    CANCELED = "canceled", "취소"


class Purchase(TimeStampedSoftDelete):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases"
    )
    purchase_status = models.CharField(
        max_length=20, choices=PurchaseStatus.choices, default=PurchaseStatus.PENDING
    )
    total_price = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "purchase"
        indexes = [
            models.Index(fields=["user", "purchase_status"], name="purchase_user_status_idx"),
        ]

    def __str__(self):
        return f"Purchase({self.pk}) - {self.purchase_status}"


class Ticket(TimeStampedSoftDelete):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets"
    )
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="tickets")
    event_time = models.ForeignKey(EventTime, on_delete=models.CASCADE, related_name="tickets")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="tickets")
    ticket_status = models.CharField(
        max_length=20, choices=TicketStatus.choices, default=TicketStatus.BOOKED
    )
    aws_face_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    face_verified_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ticket"
        indexes = [
            models.Index(fields=["user", "created_at"], name="ticket_user_created_idx"),
            models.Index(fields=["purchase"], name="ticket_purchase_idx"),
            models.Index(fields=["ticket_status"], name="ticket_status_idx"),
        ]

    def __str__(self):
        return f"Ticket({self.pk}) - {self.ticket_status}"
