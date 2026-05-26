from django.db.models import Max, Min, Prefetch, Q

from apps.events.models import Event, EventTime, Zone


def event_list_qs(keyword=None, category=None, sort="new"):
    qs = (
        Event.objects
        .filter(is_deleted=False)
        .annotate(
            min_price=Min("event_times__zones__price"),
            next_date=Min("event_times__event_date"),
        )
    )
    if keyword:
        qs = qs.filter(Q(name__icontains=keyword) | Q(artist__icontains=keyword))
    if category:
        qs = qs.filter(genre=category)
    return qs.order_by("-view_count" if sort == "popular" else "-created_at")


def event_detail(event_id):
    zones_qs = Zone.objects.filter(is_deleted=False)
    times_qs = EventTime.objects.filter(is_deleted=False).prefetch_related(
        Prefetch("zones", queryset=zones_qs)
    )
    event = (
        Event.objects
        .filter(is_deleted=False)
        .prefetch_related(Prefetch("event_times", queryset=times_qs))
        .get(pk=event_id)
    )
    price_range = Zone.objects.filter(
        event_time__event=event,
        is_deleted=False,
    ).aggregate(min=Min("price"), max=Max("price"))
    return event, price_range
