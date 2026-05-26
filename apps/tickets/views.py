import base64

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tickets.exceptions import (
    AlreadyPaid,
    AntiSpoofUnavailable,
    FaceAlreadyRegistered,
    FaceMismatch,
    SeatsUnavailable,
    ShareCountMismatch,
    TicketAlreadyCheckedIn,
    TicketNotCancelable,
)
from apps.tickets.metrics import FACE_AUTH_FAILURES, FACE_REGISTER_FAILURES
from apps.tickets.models import Purchase, Ticket, TicketStatus
from apps.tickets.serializers import (
    BuyTicketsSerializer,
    FaceStatusSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketShareSerializer,
)
from apps.tickets.services import antispoof, aws_rekognition
from apps.tickets.services.booking import book_seats, pay_purchase
from apps.tickets.services.cancellation import cancel_ticket
from apps.tickets.services.image_utils import log_image, resize_to_4_3
from apps.tickets.services.qr import generate_ticket_qr
from apps.tickets.services.sharing import share_tickets
from apps.tickets.tasks import auto_cancel_ticket

User = get_user_model()


# ──────────────────────────────────────────────────────────
# 티켓 목록 / 상세 ViewSet
# ──────────────────────────────────────────────────────────

class TicketPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/v1/tickets/        — 내 티켓 목록 (배열 반환)
    GET    /api/v1/tickets/<id>/   — 내 티켓 상세
    DELETE /api/v1/tickets/<id>/   — 티켓 취소 (좌석 복원 + 소프트 삭제)

    select_related 4단 JOIN으로 N+1 없이 2 쿼리(목록) / 1 쿼리(상세)로 처리.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Ticket.objects
            .select_related("seat__zone__event_time__event", "purchase")
            .filter(user=self.request.user, is_deleted=False)
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TicketDetailSerializer
        return TicketListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """티켓 취소: 좌석을 available로 되돌리고 소프트 삭제한다."""
        ticket = self.get_object()
        try:
            result = cancel_ticket(ticket)
        except TicketNotCancelable as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"message": "티켓이 성공적으로 취소되었습니다.", **result},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────
# 예매 / 결제 APIView
# ──────────────────────────────────────────────────────────

class BuyTicketsView(APIView):
    """
    POST /api/v1/events/<pk>/tickets/buy
    Body: { "event_time_id": 1, "seat_ids": [42, 43] }

    - transaction.atomic() 안에서 book_seats 호출 → select_for_update 보장
    - on_commit으로 Celery 태스크 등록 → 롤백 시 enqueue 차단
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = BuyTicketsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_time_id = serializer.validated_data["event_time_id"]
        seat_ids = serializer.validated_data["seat_id"]

        try:
            with transaction.atomic():
                purchase, ticket_ids = book_seats(request.user, event_time_id, seat_ids)

                def schedule(ids=ticket_ids):
                    for tid in ids:
                        auto_cancel_ticket.apply_async((tid,), countdown=300)

                transaction.on_commit(schedule)

        except SeatsUnavailable as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"purchase_id": purchase.id, "ticket_ids": ticket_ids},
            status=status.HTTP_201_CREATED,
        )


class PayPurchaseView(APIView):
    """
    PATCH /api/v1/purchases/<pk>/pay/

    - select_for_update()로 중복 결제 race 방지
    - tickets 상태 bulk update → N+1 없음
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            ticket_ids = pay_purchase(purchase_id=pk, user=request.user)
        except Purchase.DoesNotExist:
            raise Http404
        except AlreadyPaid:
            return Response(
                {"error": "이미 결제된 주문입니다."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response({"ticket_ids": ticket_ids})


# ──────────────────────────────────────────────────────────
# 얼굴 인식 API
# ──────────────────────────────────────────────────────────

def _get_ticket_for_user(ticket_id: int, user) -> Ticket:
    """본인 소유 티켓을 가져온다. 없으면 Http404."""
    try:
        return Ticket.objects.get(pk=ticket_id, user=user, is_deleted=False)
    except Ticket.DoesNotExist:
        raise Http404


def _decode_image(request) -> bytes:
    """요청 body의 'image' 필드(base64 문자열)를 bytes로 변환한다."""
    image_b64: str = request.data.get("image", "")
    if not image_b64:
        raise ValueError("image 필드가 필요합니다.")
    return base64.b64decode(image_b64)


class FaceRegisterView(APIView):
    """
    POST /api/v1/tickets/<pk>/face-register/
    Body: { "image": "<base64 JPEG>" }

    1. 안티스푸핑 검사 (실물 얼굴인지 확인)
    2. 4:3 리사이즈
    3. Rekognition index_faces → aws_face_id 저장
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)

        try:
            image_b64: str = request.data.get("image", "")
            if not image_b64:
                FACE_REGISTER_FAILURES.labels(reason="no_image").inc()
                return Response({"error": "image 필드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

            image_bytes = base64.b64decode(image_b64)
        except Exception:
            FACE_REGISTER_FAILURES.labels(reason="invalid_image").inc()
            return Response({"error": "유효하지 않은 base64 이미지입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if not antispoof.is_real_face(image_b64):
                FACE_REGISTER_FAILURES.labels(reason="spoof").inc()
                return Response({"error": "실물 얼굴이 감지되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)
        except AntiSpoofUnavailable:
            FACE_REGISTER_FAILURES.labels(reason="antispoof_down").inc()
            return Response({"error": "안티스푸핑 서버를 사용할 수 없습니다."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        resized = resize_to_4_3(image_bytes)
        log_image("face-register", resized, ticket_id=ticket.id)

        try:
            face_id = aws_rekognition.register_face(request.user, ticket, resized)
        except FaceAlreadyRegistered:
            FACE_REGISTER_FAILURES.labels(reason="duplicate").inc()
            return Response({"error": "이미 얼굴이 등록된 티켓입니다."}, status=status.HTTP_409_CONFLICT)
        except ValueError as e:
            FACE_REGISTER_FAILURES.labels(reason="no_face").inc()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "awsFaceId": face_id,
                "face_id": face_id,
                "ticket_status": TicketStatus.VERIFIED,
                "success": True,
                "message": "얼굴 등록이 성공적으로 완료되었습니다.",
            },
            status=status.HTTP_200_OK,
        )


class FaceAuthView(APIView):
    """
    POST /api/v1/tickets/<pk>/face-auth/
    Body: { "image": "<base64 JPEG>" }

    Rekognition search_faces_by_image 로 ticket.aws_face_id 와 대조.
    유사도 ≥ 99.0 이면 200, 아니면 401.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)

        if not ticket.aws_face_id:
            return Response({"error": "얼굴이 아직 등록되지 않은 티켓입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image_bytes = _decode_image(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        resized = resize_to_4_3(image_bytes)
        log_image("face-auth", resized, ticket_id=ticket.id)

        try:
            similarity = aws_rekognition.authenticate_face(ticket, resized)
        except FaceMismatch:
            FACE_AUTH_FAILURES.labels(reason="mismatch").inc()
            return Response({"error": "얼굴 인증 실패"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {
                "similarity": similarity,
                "Similarity": similarity,
                "success": True,
                "message": "얼굴 인증이 성공적으로 완료되었습니다.",
            },
            status=status.HTTP_200_OK,
        )


class FaceRegisterUpdateView(APIView):
    """
    PATCH /api/v1/tickets/<pk>/register/
    Body: { "face_verified": true }

    AWS 등록 후 DB 상태 확인용 호환 엔드포인트.
    FaceRegisterView(POST aws-register)가 이미 aws_face_id와 face_verified_at을 저장하므로
    현재 등록 상태를 그대로 반환한다.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)
        return Response(FaceStatusSerializer(ticket).data, status=status.HTTP_200_OK)


class FaceDeleteView(APIView):
    """
    DELETE /api/v1/tickets/<pk>/face/

    Rekognition 컬렉션에서 얼굴 삭제 후 DB의 aws_face_id 를 NULL 로 초기화.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)
        aws_rekognition.delete_face(ticket)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FaceStatusView(APIView):
    """
    GET /api/v1/tickets/<pk>/face-status/

    얼굴 등록 여부(aws_face_id 존재)와 등록 시각을 반환한다.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)
        return Response(FaceStatusSerializer(ticket).data, status=status.HTTP_200_OK)


class FaceCheckView(APIView):
    """
    POST /api/v1/face/check/
    Body: { "image": "<base64 JPEG>" }

    얼굴이 중앙 가이드라인 타원 안에 있는지 확인한다. (인증 불필요)
    """

    permission_classes = [AllowAny]

    def post(self, request):
        image_b64: str = request.data.get("image", "")
        if not image_b64:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        # data URI 접두사(data:image/...;base64,) 제거
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception:
            return Response({"error": "유효하지 않은 base64 이미지입니다."}, status=status.HTTP_400_BAD_REQUEST)

        in_guide = aws_rekognition.is_face_in_guide(image_bytes)
        message = (
            "얼굴이 가이드라인 안에 있습니다."
            if in_guide
            else "가이드라인 안에 얼굴이 없습니다."
        )
        return Response({"is_in_guide": in_guide, "message": message}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────────────
# 티켓 공유 / QR / 입장 처리
# ──────────────────────────────────────────────────────────

class ShareTicketsView(APIView):
    """
    POST /api/v1/tickets/<purchase_id>/share/
    Body: { "ticket_user_emails": ["a@x.com", ...] }

    본인 티켓 1장은 유지, 나머지를 지정 유저에게 양도한다 (Atomic).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = TicketShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emails = serializer.validated_data["ticket_user_emails"]

        try:
            share_tickets(purchase_id=pk, owner=request.user, emails=emails)
        except Purchase.DoesNotExist:
            raise Http404
        except ShareCountMismatch as e:
            return Response(
                {"error": "공유 티켓 수가 맞지 않음", "details": {"expected": e.expected, "given": e.given}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "일부 이메일이 존재하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Tickets shared successfully"}, status=status.HTTP_200_OK)


class TicketQRView(APIView):
    """
    GET /api/v1/tickets/<pk>/qr/

    체크인 URL을 담은 QR 코드를 base64 PNG로 반환한다.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)
        return Response({"qr_base64": generate_ticket_qr(ticket)}, status=status.HTTP_200_OK)


class CertificationView(APIView):
    """
    PATCH /api/v1/tickets/<pk>/certification/

    티켓을 입장 완료(checked_in) 상태로 전환한다.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        ticket = _get_ticket_for_user(pk, request.user)

        try:
            if ticket.ticket_status == TicketStatus.CHECKED_IN:
                raise TicketAlreadyCheckedIn()
        except TicketAlreadyCheckedIn:
            return Response(
                {"message": "이미 입장 처리된 티켓입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        Ticket.objects.filter(pk=ticket.pk).update(
            ticket_status=TicketStatus.CHECKED_IN,
            checked_in_at=now,
        )
        return Response(
            {
                "message": "티켓이 checked_in(입장 완료) 상태로 변경되었습니다.",
                "ticket": {
                    "id": ticket.pk,
                    "ticket_status": TicketStatus.CHECKED_IN,
                    "checked_in_at": now,
                },
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────
# HTML 페이지 (체크인 / 얼굴 등록)
# ──────────────────────────────────────────────────────────

class CheckinPageView(View):
    """
    GET /api/v1/tickets/<pk>/checkin/

    QR 스캔 시 진입하는 체크인 페이지. 인증 불필요(읽기 전용 표시).
    """

    def get(self, request, pk):
        ticket = (
            Ticket.objects
            .select_related("seat__zone__event_time__event")
            .filter(pk=pk, is_deleted=False)
            .first()
        )
        if ticket is None:
            return render(request, "tickets/invalid_ticket.html", status=404)
        return render(request, "tickets/checkin.html", {"ticket": ticket})


class FaceRegisterPageView(TemplateView):
    """
    GET /api/v1/tickets/face-register-page/

    얼굴 등록 안내 HTML 페이지. 인증 불필요.
    """

    template_name = "tickets/face_register.html"
