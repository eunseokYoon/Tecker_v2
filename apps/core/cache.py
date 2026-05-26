from django.core.cache import cache
from prometheus_client import Counter

CACHE_HITS = Counter(
    "cache_hits_total",
    "Cache hit/miss counter",
    ["cache", "result"],
)


def cached(key_func, timeout: int = 60, name: str = "events"):
    """
    함수 결과를 Redis 캐시에 저장하는 데코레이터.

    Usage:
        @cached(key_func=lambda pk: f"events:detail:{pk}", name="events")
        def get_event_data(pk): ...
    """
    def deco(fn):
        def wrap(*args, **kwargs):
            key = key_func(*args, **kwargs)
            value = cache.get(key)
            CACHE_HITS.labels(name, "hit" if value is not None else "miss").inc()
            if value is None:
                value = fn(*args, **kwargs)
                cache.set(key, value, timeout=timeout)
            return value
        return wrap
    return deco
