from django.conf import settings
from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.accounts.services.google import verify_google_id_token


class SignupView(APIView):
    """
    POST /auth/signup/
    Body: { "email": "...", "password": "...", "name": "..." }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        name = request.data.get("name", "").strip()

        if not email or not password:
            return Response(
                {"error": "이메일과 비밀번호를 입력하세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"email": ["이미 사용 중인 이메일입니다."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            name=name,
        )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /auth/login/
    Body: { "email": "...", "password": "..." }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {"error": "이메일과 비밀번호를 입력하세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "이메일 또는 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class GoogleLoginView(APIView):
    """
    POST /auth/google/
    Body: { "id_token": "<Google ID Token>" }

    1. Google tokeninfo로 ID Token 검증
    2. google_sub 기준으로 User get_or_create
    3. access + refresh 토큰을 body로 반환 (클라이언트가 Keychain/Keystore에 보관)
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response(
                {"error": "id_token이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = verify_google_id_token(id_token)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        sub = payload["sub"]
        email = payload.get("email", "")
        name = payload.get("name", "")

        try:
            user, _ = User.objects.get_or_create(
                google_sub=sub,
                defaults={
                    "email": email,
                    "username": email,
                    "name": name,
                },
            )
        except IntegrityError:
            # 같은 email을 가진 기존 계정에 google_sub 연결
            try:
                user = User.objects.get(email=email)
                user.google_sub = sub
                user.save(update_fields=["google_sub"])
            except User.DoesNotExist:
                return Response(
                    {"error": "계정 생성 중 오류가 발생했습니다."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class TokenRefreshView(APIView):
    """
    POST /auth/refresh/
    Body: { "refresh": "<refresh token>" }

    클라이언트가 Keychain/Keystore에서 꺼낸 refresh 토큰으로 새 access 토큰을 발급한다.
    ROTATE_REFRESH_TOKENS=True 이면 새 refresh 토큰도 body에 함께 반환한다.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token_str = request.data.get("refresh")
        if not refresh_token_str:
            return Response(
                {"error": "refresh 토큰이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token_str)
            access = str(refresh.access_token)
        except TokenError:
            return Response(
                {"error": "유효하지 않거나 만료된 refresh 토큰입니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data: dict = {"access": access}

        # ROTATE_REFRESH_TOKENS=True 인 경우 새 refresh 토큰도 반환
        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):
            data["refresh"] = str(refresh)

        return Response(data)


class LogoutView(APIView):
    """
    POST /auth/logout/
    Body: { "refresh": "<refresh token>" }

    refresh 토큰을 블랙리스트에 등록한다.
    클라이언트는 응답 수신 후 Keychain/Keystore에서 토큰을 직접 삭제해야 한다.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token_str = request.data.get("refresh")

        if refresh_token_str:
            try:
                token = RefreshToken(refresh_token_str)
                token.blacklist()
            except TokenError:
                pass  # 이미 블랙리스트에 있거나 만료된 경우 무시

        return Response({"message": "로그아웃되었습니다."})
