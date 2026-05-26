import os

import requests

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

# iOS와 Android 클라이언트 ID를 각각 환경변수로 관리
# 예: GOOGLE_CLIENT_IDS=ios-id.apps.googleusercontent.com,android-id.apps.googleusercontent.com
_raw = os.environ.get("GOOGLE_CLIENT_IDS", os.environ.get("GOOGLE_CLIENT_ID", ""))
_ALLOWED_CLIENT_IDS: set[str] = {cid.strip() for cid in _raw.split(",") if cid.strip()}


def verify_google_id_token(id_token: str) -> dict:
    """
    Google tokeninfo 엔드포인트로 ID Token을 검증하고 payload를 반환한다.
    검증 실패 시 ValueError를 발생시킨다.

    반환 예시:
        {"sub": "116...", "email": "alice@gmail.com", "email_verified": "true", ...}
    """
    try:
        resp = requests.get(
            GOOGLE_TOKENINFO_URL,
            params={"id_token": id_token},
            timeout=5,
        )
    except requests.RequestException as e:
        raise ValueError(f"Google tokeninfo 요청 실패: {e}") from e

    if resp.status_code != 200:
        raise ValueError("유효하지 않은 Google ID Token")

    payload = resp.json()

    if "error" in payload:
        raise ValueError(f"Google 토큰 오류: {payload['error']}")

    # iOS / Android 클라이언트 ID 중 하나와 일치해야 함
    # 환경변수 미설정(테스트 환경)이면 검사 생략
    if _ALLOWED_CLIENT_IDS and payload.get("aud") not in _ALLOWED_CLIENT_IDS:
        raise ValueError("토큰 audience 불일치 — 허용되지 않은 클라이언트")

    # 이메일 인증 여부 확인
    if payload.get("email_verified") not in ("true", True):
        raise ValueError("이메일이 인증되지 않은 Google 계정")

    return payload
