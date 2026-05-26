from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tickets.views import (
    BuyTicketsView,
    CertificationView,
    CheckinPageView,
    FaceAuthView,
    FaceCheckView,
    FaceDeleteView,
    FaceRegisterPageView,
    FaceRegisterUpdateView,
    FaceRegisterView,
    FaceStatusView,
    PayPurchaseView,
    ShareTicketsView,
    TicketQRView,
    TicketViewSet,
)

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    # 얼굴 등록 안내 페이지 — <int:pk> 라우트보다 먼저 (리터럴 우선 매칭)
    path("tickets/face-register-page/", FaceRegisterPageView.as_view(), name="face-register-page"),
    path("", include(router.urls)),
    path("events/view/<int:pk>/tickets/buy", BuyTicketsView.as_view(), name="buy-tickets"),
    path("events/view/<int:pk>/tickets/pay/", PayPurchaseView.as_view(), name="pay-purchase"),
    # 티켓 공유 / QR / 입장
    path("tickets/<int:pk>/share/", ShareTicketsView.as_view(), name="ticket-share"),
    path("tickets/<int:pk>/qr/", TicketQRView.as_view(), name="ticket-qr"),
    path("tickets/<int:pk>/qr", TicketQRView.as_view(), name="ticket-qr-noslash"),
    path("tickets/<int:pk>/checkin/", CheckinPageView.as_view(), name="ticket-checkin"),
    path("tickets/<int:pk>/certification/", CertificationView.as_view(), name="ticket-certification"),
    # 얼굴 인식 (프론트엔드 호환 URL + tecker_v2 내부 URL)
    path("tickets/<int:pk>/aws-register/", FaceRegisterView.as_view(), name="aws-face-register"),
    path("tickets/<int:pk>/register/", FaceRegisterUpdateView.as_view(), name="face-register-update"),
    path("tickets/<int:pk>/aws-auth/", FaceAuthView.as_view(), name="aws-face-auth"),
    path("tickets/<int:pk>/auth/", FaceStatusView.as_view(), name="face-auth-status"),
    path("tickets/<int:pk>/face-register/", FaceRegisterView.as_view(), name="face-register"),
    path("tickets/<int:pk>/face-auth/", FaceAuthView.as_view(), name="face-auth"),
    path("tickets/<int:pk>/face-status/", FaceStatusView.as_view(), name="face-status"),
    path("tickets/<int:pk>/face/", FaceDeleteView.as_view(), name="face-delete"),
    path("face/check/", FaceCheckView.as_view(), name="face-check"),
]
