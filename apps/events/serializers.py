from rest_framework import serializers


class ZoneSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    rank = serializers.IntegerField()
    price = serializers.IntegerField()


class EventTimeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    event_date = serializers.DateTimeField()
    zones = ZoneSerializer(many=True)


class ScheduleSerializer(serializers.Serializer):
    """프론트엔드 EventDetailPage / SeatSelectPage 호환 공연 일정 형식."""

    event_time_id = serializers.IntegerField(source="id")
    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    zone_ids = serializers.SerializerMethodField()
    zones = ZoneSerializer(many=True)

    def get_date(self, obj) -> str:
        return obj.event_date.strftime("%Y-%m-%d")

    def get_start_time(self, obj) -> str:
        return obj.event_date.strftime("%H:%M:%S")

    def get_end_time(self, obj) -> str:
        return ""

    def get_zone_ids(self, obj) -> list:
        return [zone.id for zone in obj.zones.all()]


class EventListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    artist = serializers.CharField()
    genre = serializers.CharField()
    location = serializers.CharField()
    view_count = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    min_price = serializers.IntegerField()
    next_date = serializers.DateTimeField()
    # 프론트엔드 호환 필드
    price = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="next_date", allow_null=True)
    status = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_thumbnail(self, obj):
        if obj.thumbnail and obj.thumbnail.name:
            return obj.thumbnail.name
        return None

    def get_price(self, obj) -> int:
        return obj.min_price or 0

    def get_status(self, obj) -> str:
        return "예매중"


class EventDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    artist = serializers.CharField()
    genre = serializers.CharField()
    location = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    max_reserve = serializers.IntegerField(allow_null=True)
    view_count = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    event_times = EventTimeSerializer(many=True)
    schedules = ScheduleSerializer(source="event_times", many=True)
    # 프론트엔드 호환 필드
    price = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_thumbnail(self, obj):
        if obj.thumbnail and obj.thumbnail.name:
            return obj.thumbnail.name
        return None

    def get_price(self, obj) -> int:
        prices = [
            zone.price
            for et in obj.event_times.all()
            for zone in et.zones.all()
        ]
        return min(prices) if prices else 0

    def get_date(self, obj) -> str | None:
        dates = [et.event_date for et in obj.event_times.all()]
        if not dates:
            return None
        return min(dates).strftime("%Y-%m-%d")

    def get_status(self, obj) -> str:
        return "예매중"
