import functools

import boto3
from django.conf import settings
from django.utils import timezone

from apps.core.metrics import AWS_REK
from apps.tickets.exceptions import FaceAlreadyRegistered, FaceMismatch
from apps.tickets.models import Ticket, TicketStatus

# 얼굴이 들어가야 하는 중앙 타원 가이드 (BoundingBox 좌표계, 0~1 정규화)
_GUIDE_CENTER = (0.5, 0.45)
_GUIDE_RADIUS = (0.32, 0.40)


@functools.lru_cache(maxsize=1)
def _client():
    """프로세스당 1회만 boto3 Rekognition 클라이언트를 생성한다."""
    return boto3.client(
        "rekognition",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def _collection_id() -> str:
    return settings.REKOGNITION_COLLECTION_ID


def register_face(user, ticket: Ticket, image_bytes: bytes) -> str:
    """
    Rekognition 컬렉션에 얼굴을 등록하고 aws_face_id를 DB에 저장한다.

    중복 등록 여부를 DB O(1) 조회로 판단 → list_faces 풀스캔 제거.
    """
    if ticket.aws_face_id:
        raise FaceAlreadyRegistered(ticket_id=ticket.id)

    AWS_REK.labels(op="index_faces").inc()
    res = _client().index_faces(
        CollectionId=_collection_id(),
        Image={"Bytes": image_bytes},
        ExternalImageId=f"user_{user.id}_ticket_{ticket.id}",
        DetectionAttributes=["DEFAULT"],
    )

    face_records = res.get("FaceRecords", [])
    if not face_records:
        raise ValueError("이미지에서 얼굴을 감지하지 못했습니다.")

    face_id: str = face_records[0]["Face"]["FaceId"]
    # 등록 성공 시 aws_face_id 저장 + 상태를 VERIFIED로 승격 (단일 UPDATE)
    Ticket.objects.filter(pk=ticket.id).update(
        aws_face_id=face_id,
        ticket_status=TicketStatus.VERIFIED,
        face_verified_at=timezone.now(),
    )
    return face_id


def is_face_in_guide(image_bytes: bytes) -> bool:
    """
    이미지에서 얼굴을 감지하여 중앙 타원 가이드 안에 있는지 판정한다.

    detect_faces의 BoundingBox 중심이 _GUIDE 타원 내부면 True.
    얼굴이 없으면 False.
    """
    AWS_REK.labels(op="detect_faces").inc()
    res = _client().detect_faces(
        Image={"Bytes": image_bytes},
        Attributes=["DEFAULT"],
    )
    faces = res.get("FaceDetails", [])
    if not faces:
        return False

    # 가장 큰 얼굴 기준
    box = max(
        faces, key=lambda f: f["BoundingBox"]["Width"] * f["BoundingBox"]["Height"]
    )["BoundingBox"]
    cx = box["Left"] + box["Width"] / 2
    cy = box["Top"] + box["Height"] / 2

    nx = (cx - _GUIDE_CENTER[0]) / _GUIDE_RADIUS[0]
    ny = (cy - _GUIDE_CENTER[1]) / _GUIDE_RADIUS[1]
    return (nx * nx + ny * ny) <= 1.0


def authenticate_face(ticket: Ticket, image_bytes: bytes) -> float:
    """
    이미지로 컬렉션을 검색하여 ticket.aws_face_id와 대조한다.

    유사도 ≥ 99.0 이어야 통과, 아니면 FaceMismatch.
    """
    AWS_REK.labels(op="search_faces_by_image").inc()
    res = _client().search_faces_by_image(
        CollectionId=_collection_id(),
        Image={"Bytes": image_bytes},
        MaxFaces=5,
        FaceMatchThreshold=80,
    )

    for match in res.get("FaceMatches", []):
        if match["Face"]["FaceId"] == ticket.aws_face_id and match["Similarity"] >= 99.0:
            return match["Similarity"]

    raise FaceMismatch()


def delete_face(ticket: Ticket) -> None:
    """컬렉션에서 얼굴을 삭제하고 DB의 aws_face_id를 NULL로 초기화한다."""
    if not ticket.aws_face_id:
        return

    AWS_REK.labels(op="delete_faces").inc()
    _client().delete_faces(
        CollectionId=_collection_id(),
        FaceIds=[ticket.aws_face_id],
    )
    Ticket.objects.filter(pk=ticket.id).update(aws_face_id=None)
