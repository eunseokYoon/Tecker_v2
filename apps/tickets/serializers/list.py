from rest_framework import serializers


class TicketListSerializer(serializers.Serializer):
    """
    티켓 목록 직렬화.
    모든 nested 필드를 source="..." 로 명시 → ModelSerializer 자동 추가 쿼리 없음.
    select_related("seat__zone__event_time__event", "purchase")로 미리 로드된 객체만 접근.
    """

    id = serializers.IntegerField()
    ticket_status = serializers.CharField()

    # Event 정보 (4단 JOIN: seat → zone → event_time → event)
    event_name = serializers.CharField(source="seat.zone.event_time.event.name")
    event_date = serializers.DateTimeField(source="seat.zone.event_time.event_date")
    event_location = serializers.CharField(source="seat.zone.event_time.event.location")
    thumbnail = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    # Zone / Seat 정보
    zone_name = serializers.CharField(source="seat.zone.name")
    zone_rank = serializers.IntegerField(source="seat.zone.rank")
    seat_number = serializers.CharField(source="seat.seat_number")
    seat_rank = serializers.CharField(source="seat.zone.name")
    ticket_price = serializers.IntegerField(source="seat.zone.price")

    # Purchase
    purchase_id = serializers.IntegerField(source="purchase.id")

    # 얼굴 인식 상태
    face_verified = serializers.SerializerMethodField()
    verified_at = serializers.DateTimeField(source="face_verified_at", allow_null=True)

    def get_thumbnail(self, obj):
        thumbnail = obj.seat.zone.event_time.event.thumbnail
        if thumbnail and thumbnail.name:
            return thumbnail.name
        return None

    def get_image_url(self, obj):
        return self.get_thumbnail(obj)

    def get_face_verified(self, obj) -> bool:
        return bool(obj.aws_face_id)
