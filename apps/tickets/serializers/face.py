from rest_framework import serializers


class TicketShareSerializer(serializers.Serializer):
    """티켓 공유(양도) 요청 검증."""

    ticket_user_emails = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
    )


class FaceStatusSerializer(serializers.Serializer):
    """얼굴 등록 상태 응답."""

    ticket_id = serializers.IntegerField(source="id")
    face_verified = serializers.SerializerMethodField()
    face_verified_at = serializers.DateTimeField(allow_null=True)
    ticket_status = serializers.CharField()

    def get_face_verified(self, obj) -> bool:
        return bool(obj.aws_face_id)
