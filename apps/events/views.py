import hashlib
import json

from django.core.cache import cache
from django.db.models import F
from django.http import Http404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.cache import CACHE_HITS
from apps.events.models import Event, Seat, Zone
from apps.events.queries import event_detail, event_list_qs
from apps.events.serializers import EventDetailSerializer, EventListSerializer

CACHE_TIMEOUT = 60  # 초


class EventPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class EventListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = {
            k: request.query_params.get(k, "")
            for k in ["keyword", "category", "sort", "page", "limit"]
        }
        key = "events:list:" + hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()

        data = cache.get(key)
        CACHE_HITS.labels("events", "hit" if data is not None else "miss").inc()

        if data is None:
            qs = event_list_qs(
                keyword=params["keyword"] or None,
                category=params["category"] or None,
                sort=params["sort"] or "new",
            )
            paginator = EventPagination()
            page_qs = paginator.paginate_queryset(qs, request)
            serializer = EventListSerializer(page_qs, many=True)
            page_num = int(params["page"]) if params["page"] else 1
            limit_num = int(params["limit"]) if params["limit"] else paginator.page_size
            data = {
                "page": page_num,
                "limit": limit_num,
                "events": serializer.data,
                "totalCount": paginator.page.paginator.count,
            }
            cache.set(key, data, timeout=CACHE_TIMEOUT)

        return Response(data)


class EventDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        key = f"events:detail:{pk}"
        data = cache.get(key)
        CACHE_HITS.labels("events_detail", "hit" if data is not None else "miss").inc()

        if data is None:
            try:
                event, price_range = event_detail(pk)
            except Event.DoesNotExist:
                raise Http404
            serialized = EventDetailSerializer(event).data
            data = dict(serialized)
            data["price_range"] = price_range
            cache.set(key, data, timeout=CACHE_TIMEOUT)

        # view_count 는 캐시와 무관하게 매 요청마다 atomic 증가
        Event.objects.filter(pk=pk).update(view_count=F("view_count") + 1)

        return Response(data)


class SeatListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            zone = Zone.objects.select_related("event_time").get(pk=pk, is_deleted=False)
        except Zone.DoesNotExist:
            raise Http404

        seats = (
            Seat.objects
            .filter(zone=zone, is_deleted=False)
            .values("id", "seat_number", "seat_status")
        )
        available_count = zone.available_count
        event_date_str = zone.event_time.event_date.isoformat()
        data = [
            {
                "seat_id": s["id"],
                "seat_number": s["seat_number"],
                "seat_status": s["seat_status"],
                "price": zone.price,
                "event_time_id": zone.event_time_id,
                "available_count": available_count,
                "date": event_date_str,
            }
            for s in seats
        ]
        return Response({"statusCode": 200, "message": "success", "data": data})
