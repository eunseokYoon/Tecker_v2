"""Phase 11 — 얼굴 가이드라인 체크 (POST /face/check/)"""

import base64
import io

import pytest
from PIL import Image

from apps.tickets.services import aws_rekognition


@pytest.fixture()
def sample_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), color=(120, 120, 120)).save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.mark.django_db
def test_face_in_guide_returns_true(api_client, sample_b64, monkeypatch):
    monkeypatch.setattr(aws_rekognition, "is_face_in_guide", lambda _: True)

    res = api_client.post("/api/v1/face/check/", {"image": sample_b64}, format="json")

    assert res.status_code == 200
    assert res.json()["is_in_guide"] is True


@pytest.mark.django_db
def test_face_out_of_guide_returns_false(api_client, sample_b64, monkeypatch):
    monkeypatch.setattr(aws_rekognition, "is_face_in_guide", lambda _: False)

    res = api_client.post("/api/v1/face/check/", {"image": sample_b64}, format="json")

    assert res.status_code == 200
    assert res.json()["is_in_guide"] is False


@pytest.mark.django_db
def test_face_check_no_image_returns_400(api_client):
    res = api_client.post("/api/v1/face/check/", {}, format="json")
    assert res.status_code == 400


def test_is_face_in_guide_geometry(monkeypatch):
    """detect_faces BoundingBox 중심이 타원 안/밖일 때의 판정 검증."""

    class _FakeClient:
        def __init__(self, box):
            self._box = box

        def detect_faces(self, **_kw):
            return {"FaceDetails": [{"BoundingBox": self._box}]}

    # 중앙 정렬된 얼굴 → 가이드 안
    centered = {"Left": 0.35, "Top": 0.25, "Width": 0.30, "Height": 0.40}
    monkeypatch.setattr(aws_rekognition, "_client", lambda: _FakeClient(centered))
    assert aws_rekognition.is_face_in_guide(b"x") is True

    # 좌상단으로 치우친 얼굴 → 가이드 밖
    offset = {"Left": 0.0, "Top": 0.0, "Width": 0.15, "Height": 0.20}
    monkeypatch.setattr(aws_rekognition, "_client", lambda: _FakeClient(offset))
    assert aws_rekognition.is_face_in_guide(b"x") is False
