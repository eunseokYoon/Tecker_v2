from django.db import models

from apps.core.models import TimeStampedSoftDelete


class GenreChoices(models.TextChoices):
    CONCERT = "concert", "콘서트"
    MUSICAL = "musical", "뮤지컬"
    PLAY = "play", "연극"
    SPORTS = "sports", "스포츠"
    ETC = "etc", "기타"


class SeatStatus(models.TextChoices):
    AVAILABLE = "available", "예매가능"
    BOOKED = "booked", "예매됨"
    RESERVED = "reserved", "결제완료"


class Event(TimeStampedSoftDelete):
    name = models.CharField(max_length=200)
    artist = models.CharField(max_length=100)
    genre = models.CharField(max_length=20, choices=GenreChoices.choices, default=GenreChoices.CONCERT)
    location = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    max_reserve = models.PositiveIntegerField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    thumbnail = models.ImageField(upload_to="events/thumbnails/", null=True, blank=True)

    class Meta:
        db_table = "event"
        indexes = [
            models.Index(fields=["is_deleted", "created_at"], name="event_deleted_created_idx"),
            models.Index(fields=["genre"], name="event_genre_idx"),
            models.Index(fields=["view_count"], name="event_view_count_idx"),
        ]

    def __str__(self):
        return self.name


class EventTime(TimeStampedSoftDelete):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_times")
    event_date = models.DateTimeField()

    class Meta:
        db_table = "event_time"
        indexes = [
            models.Index(fields=["event", "event_date"], name="eventtime_event_date_idx"),
        ]

    def __str__(self):
        return f"{self.event.name} - {self.event_date}"


class Zone(TimeStampedSoftDelete):
    event_time = models.ForeignKey(EventTime, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=100)
    rank = models.PositiveSmallIntegerField(default=1)
    price = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "zone"
        indexes = [
            models.Index(fields=["event_time", "rank"], name="zone_eventtime_rank_idx"),
        ]

    def __str__(self):
        return f"{self.event_time} - {self.name}"

    @property
    def available_count(self):
        return self.seats.filter(seat_status=SeatStatus.AVAILABLE, is_deleted=False).count()


class Seat(TimeStampedSoftDelete):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=20)
    seat_status = models.CharField(
        max_length=20, choices=SeatStatus.choices, default=SeatStatus.AVAILABLE
    )

    class Meta:
        db_table = "seat"
        indexes = [
            models.Index(fields=["zone", "seat_status"], name="seat_zone_status_idx"),
        ]

    def __str__(self):
        return f"{self.zone} - {self.seat_number}"
