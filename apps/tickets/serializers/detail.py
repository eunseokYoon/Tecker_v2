from rest_framework import serializers


class TicketDetailSerializer(serializers.Serializer):
    """
    티켓 상세 직렬화.
    목록 필드에 추가로 artist, genre, price, aws_face_id 포함.
    """

    id = serializers.IntegerField()
    ticket_status = serializers.CharField()
    aws_face_id = serializers.CharField(allow_null=True)

    # Event 정보
    event_name = serializers.CharField(source="seat.zone.event_time.event.name")
    event_date = serializers.DateTimeField(source="seat.zone.event_time.event_date")
    event_location = serializers.CharField(source="seat.zone.event_time.event.location")
    artist = serializers.CharField(source="seat.zone.event_time.event.artist")
    genre = serializers.CharField(source="seat.zone.event_time.event.genre")
    thumbnail = serializers.SerializerMethodField()

    # Zone / Seat 정보
    zone_name = serializers.CharField(source="seat.zone.name")
    zone_rank = serializers.IntegerField(source="seat.zone.rank")
    zone_price = serializers.IntegerField(source="seat.zone.price")
    seat_number = serializers.CharField(source="seat.seat_number")
    seat_rank = serializers.CharField(source="seat.zone.name")
    ticket_price = serializers.IntegerField(source="seat.zone.price")
    image_url = serializers.SerializerMethodField()

    # Purchase
    purchase_id = serializers.IntegerField(source="purchase.id")
    purchase_status = serializers.CharField(source="purchase.purchase_status")

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
