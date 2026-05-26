import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.events.models import Event, EventTime, GenreChoices, Seat, SeatStatus, Zone
from apps.tickets.models import Purchase, PurchaseStatus, Ticket, TicketStatus


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.io")
    name = factory.Faker("name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Faker("sentence", nb_words=3)
    artist = factory.Faker("name")
    genre = GenreChoices.CONCERT
    location = "Seoul"
    view_count = 0

    @classmethod
    def create_with_full_tree(cls, num_times=5, num_zones=3, num_seats=20):
        event = cls.create()
        for _ in range(num_times):
            event_time = EventTimeFactory(event=event)
            for _ in range(num_zones):
                zone = ZoneFactory(event_time=event_time)
                for _ in range(num_seats):
                    SeatFactory(zone=zone)
        return event


class EventTimeFactory(DjangoModelFactory):
    class Meta:
        model = EventTime

    event = factory.SubFactory(EventFactory)
    event_date = factory.Faker("future_datetime", tzinfo=None)


class ZoneFactory(DjangoModelFactory):
    class Meta:
        model = Zone

    event_time = factory.SubFactory(EventTimeFactory)
    name = factory.Sequence(lambda n: f"Zone-{n}")
    rank = factory.Sequence(lambda n: n + 1)
    price = 50000

    @factory.post_generation
    def num_seats(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for i in range(extracted):
            SeatFactory(zone=self, seat_number=f"S{i:03d}")


class SeatFactory(DjangoModelFactory):
    class Meta:
        model = Seat

    zone = factory.SubFactory(ZoneFactory)
    seat_number = factory.Sequence(lambda n: f"A{n:03d}")
    seat_status = SeatStatus.AVAILABLE


class PurchaseFactory(DjangoModelFactory):
    class Meta:
        model = Purchase

    user = factory.SubFactory(UserFactory)
    purchase_status = PurchaseStatus.PENDING
    total_price = 50000


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    user = factory.SubFactory(UserFactory)
    purchase = factory.SubFactory(PurchaseFactory)
    event_time = factory.SubFactory(EventTimeFactory)
    seat = factory.SubFactory(SeatFactory)
    ticket_status = TicketStatus.BOOKED
