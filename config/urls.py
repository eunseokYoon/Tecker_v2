from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("", include("django_prometheus.urls")),
    # API 문서
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API
    path("auth/", include("apps.accounts.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),  # 프론트 에뮬레이터용 단일 base URL
    path("api/v1/", include("apps.events.urls")),
    path("api/v1/", include("apps.tickets.urls")),
]
