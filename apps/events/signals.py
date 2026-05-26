from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.events.models import Event, EventTime, Zone


def _invalidate_events(*_args, **_kwargs):
    """
    Event/EventTime/Zone 변경 시 이벤트 관련 캐시를 전부 무효화한다.

    delete_pattern 은 django-redis 전용 API(SCAN 기반).
    LocMemCache(테스트용) 는 해당 메서드가 없으므로 AttributeError 시 전체 clear.
    """
    try:
        cache.delete_pattern("events:*")
    except AttributeError:
        cache.clear()


for _model in (Event, EventTime, Zone):
    post_save.connect(_invalidate_events, sender=_model)
    post_delete.connect(_invalidate_events, sender=_model)
