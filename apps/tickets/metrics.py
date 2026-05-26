from prometheus_client import Counter

FACE_REGISTER_FAILURES = Counter(
    "face_register_failures_total",
    "얼굴 등록 실패 횟수",
    ["reason"],
)

FACE_AUTH_FAILURES = Counter(
    "face_auth_failures_total",
    "얼굴 인증 실패 횟수",
    ["reason"],
)
