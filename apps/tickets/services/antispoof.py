import requests
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from apps.core.metrics import ANTISPOOF_OUTAGE
from apps.tickets.exceptions import AntiSpoofUnavailable


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.2, max=2),
    # 함수가 RequestException 을 AntiSpoofUnavailable 로 변환해 던지므로
    # 재시도 조건도 AntiSpoofUnavailable 기준이어야 한다.
    retry=retry_if_exception_type(AntiSpoofUnavailable),
    reraise=True,
)
def is_real_face(image_b64: str) -> bool:
    """
    안티스푸핑 서버에 이미지를 보내 실제 얼굴 여부를 반환한다.

    서버 장애 시 0.2s → 0.4s → 0.8s 지수 백오프로 3회 재시도 후
    AntiSpoofUnavailable 을 발생시킨다.
    """
    try:
        resp = requests.post(
            f"{settings.AI_SERVER_URL}/predict",
            json={"image": image_b64},
            timeout=3,
        )
        resp.raise_for_status()
        return resp.json().get("label") == "real"
    except requests.RequestException as exc:
        ANTISPOOF_OUTAGE.inc()
        raise AntiSpoofUnavailable(str(exc)) from exc
