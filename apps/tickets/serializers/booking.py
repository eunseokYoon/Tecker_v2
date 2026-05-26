from rest_framework import serializers


class BuyTicketsSerializer(serializers.Serializer):
    event_time_id = serializers.IntegerField()
    seat_id = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=10,
    )
