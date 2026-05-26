"""
Phase 6 — 얼굴 등록 단위 테스트

핵심 검증
- register_face 호출 시 list_faces 가 0회 호출되는가  (DB dedupe)
- 동일 티켓 중복 등록 시 409 반환
- antispoof 응답이 "fake" 이면 400 반환
"""

import base64
import io

import pytest
from PIL import Image

from tests.factories import TicketFactory, UserFactory


# ── 공용 이미지 픽스처 ────────────────────────────────────────

@pytest.fixture()
def sample_jpeg_b64() -> str:
    """800×600 JPEG를 base64 로 인코딩한 최소 샘플."""
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), color=(100, 150, 200)).save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


class _FakeRekognition:
    """Rekognition 클라이언트 스텁 — 호출 횟수를 기록한다.

    moto 5.x 는 Rekognition index_faces/list_faces 를 구현하지 않으므로
    직접 스텁을 사용한다.
    """

    def __init__(self):
        self.calls = {"list_faces": 0, "index_faces": 0}

    def list_faces(self, *a, **kw):
        self.calls["list_faces"] += 1
        return {"Faces": []}

    def index_faces(self, *a, **kw):
        self.calls["index_faces"] += 1
        return {"FaceRecords": [{"Face": {"FaceId": "fake-face-id-123"}}]}


# ── 테스트 ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_register_does_not_call_list_faces(authed_client, sample_jpeg_b64, monkeypatch):
    """
    등록 API는 list_faces를 호출하지 않고 DB의 aws_face_id 컬럼으로만
    중복을 판단해야 한다. (Phase 6) + 등록 성공 시 VERIFIED 승격 (Phase 11)
    """
    from apps.tickets.models import TicketStatus
    from apps.tickets.services import aws_rekognition

    ticket = TicketFactory(aws_face_id=None)
    fake = _FakeRekognition()

    monkeypatch.setattr(aws_rekognition, "_client", lambda: fake)
    monkeypatch.setattr("apps.tickets.services.antispoof.is_real_face", lambda _: True)

    resp = authed_client(ticket.user).post(
        f"/api/v1/tickets/{ticket.id}/face-register/",
        {"image": sample_jpeg_b64},
        format="json",
    )

    assert resp.status_code == 200
    assert fake.calls["list_faces"] == 0, "list_faces 가 호출되면 안 됩니다."
    assert fake.calls["index_faces"] == 1

    # Phase 11: 등록 성공 시 상태가 VERIFIED로 승격되어야 한다
    ticket.refresh_from_db()
    assert ticket.ticket_status == TicketStatus.VERIFIED
    assert ticket.aws_face_id == "fake-face-id-123"
    assert ticket.face_verified_at is not None


@pytest.mark.django_db
def test_register_duplicate_returns_409(authed_client, sample_jpeg_b64, monkeypatch):
    """
    aws_face_id 가 이미 설정된 티켓에 다시 등록 요청하면 409를 반환해야 한다.
    """
    ticket = TicketFactory(aws_face_id="existing-face-id")

    monkeypatch.setattr(
        "apps.tickets.services.antispoof.is_real_face",
        lambda _: True,
    )

    client = authed_client(ticket.user)
    resp = client.post(
        f"/api/v1/tickets/{ticket.id}/face-register/",
        {"image": sample_jpeg_b64},
        format="json",
    )

    assert resp.status_code == 409


@pytest.mark.django_db
def test_register_fake_face_returns_400(authed_client, sample_jpeg_b64, monkeypatch):
    """
    안티스푸핑 서버가 fake 를 반환하면 400 을 반환해야 한다.
    """
    ticket = TicketFactory(aws_face_id=None)

    monkeypatch.setattr(
        "apps.tickets.services.antispoof.is_real_face",
        lambda _: False,
    )

    client = authed_client(ticket.user)
    resp = client.post(
        f"/api/v1/tickets/{ticket.id}/face-register/",
        {"image": sample_jpeg_b64},
        format="json",
    )

    assert resp.status_code == 400


@pytest.mark.django_db
def test_register_antispoof_down_returns_503(authed_client, sample_jpeg_b64, monkeypatch):
    """
    안티스푸핑 서버가 다운되면 503을 반환해야 한다.
    """
    from apps.tickets.exceptions import AntiSpoofUnavailable

    ticket = TicketFactory(aws_face_id=None)

    monkeypatch.setattr(
        "apps.tickets.services.antispoof.is_real_face",
        lambda _: (_ for _ in ()).throw(AntiSpoofUnavailable("connection refused")),
    )

    client = authed_client(ticket.user)
    resp = client.post(
        f"/api/v1/tickets/{ticket.id}/face-register/",
        {"image": sample_jpeg_b64},
        format="json",
    )

    assert resp.status_code == 503
