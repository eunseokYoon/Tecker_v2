import pytest
from django.core.exceptions import ValidationError

from apps.events.models import Event, SeatStatus
from apps.tickets.models import Ticket, TicketStatus
from tests.factories import (
    EventFactory,
    SeatFactory,
    TicketFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestTicket:
    def test_status_default_is_booked(self):
        ticket = TicketFactory()
        assert ticket.ticket_status == TicketStatus.BOOKED

    def test_invalid_status_raises_validation_error(self):
        ticket = TicketFactory()
        ticket.ticket_status = "invalid_value"
        with pytest.raises(ValidationError):
            ticket.full_clean()

    def test_aws_face_id_is_nullable(self):
        ticket = TicketFactory()
        assert ticket.aws_face_id is None

    def test_aws_face_id_field_has_db_index(self):
        field = Ticket._meta.get_field("aws_face_id")
        assert field.db_index is True

    def test_aws_face_id_can_be_set(self):
        ticket = TicketFactory(aws_face_id="face-abc-123")
        assert ticket.aws_face_id == "face-abc-123"


@pytest.mark.django_db
class TestSoftDelete:
    def test_default_manager_excludes_deleted(self):
        event = EventFactory(is_deleted=True)
        assert event not in list(Event.objects.all())

    def test_all_objects_includes_deleted(self):
        event = EventFactory(is_deleted=True)
        assert event in list(Event.all_objects.all())

    def test_soft_delete_method(self):
        event = EventFactory()
        assert Event.objects.filter(pk=event.pk).exists()
        event.soft_delete()
        assert not Event.objects.filter(pk=event.pk).exists()
        assert Event.all_objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
class TestEvent:
    def test_genre_choices_applied(self):
        event = EventFactory(genre="concert")
        assert event.genre == "concert"

    def test_invalid_genre_raises_validation_error(self):
        event = EventFactory()
        event.genre = "invalid_genre"
        with pytest.raises(ValidationError):
            event.full_clean()

    def test_view_count_default_zero(self):
        event = EventFactory()
        assert event.view_count == 0


@pytest.mark.django_db
class TestSeat:
    def test_status_default_available(self):
        seat = SeatFactory()
        assert seat.seat_status == SeatStatus.AVAILABLE

    def test_available_count_property(self):
        from tests.factories import ZoneFactory

        zone = ZoneFactory()
        SeatFactory(zone=zone, seat_status=SeatStatus.AVAILABLE)
        SeatFactory(zone=zone, seat_status=SeatStatus.AVAILABLE)
        SeatFactory(zone=zone, seat_status=SeatStatus.BOOKED)
        assert zone.available_count == 2


@pytest.mark.django_db
class TestUser:
    def test_email_unique(self):
        from django.db import IntegrityError

        user = UserFactory(email="dup@test.io")
        with pytest.raises(IntegrityError):
            UserFactory(email="dup@test.io")

    def test_meta_db_table(self):
        from apps.accounts.models import User

        assert User._meta.db_table == "user"

    def test_google_sub_nullable(self):
        user = UserFactory()
        assert user.google_sub is None
