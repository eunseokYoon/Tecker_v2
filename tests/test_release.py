"""
Phase 10 — 릴리즈 검증 테스트

Dockerfile 구조, CI 설정, Nginx 보안 헤더를 파일 파싱으로 검증한다.
인프라 코드가 의도한 패턴을 유지하고 있는지 회귀 방지.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_web_dockerfile_is_multi_stage():
    text = (ROOT / "docker/web.Dockerfile").read_text()
    assert text.count("FROM ") >= 2, "multi-stage build 아님"
    assert "USER app" in text, "비루트 사용자 없음"
    assert "HEALTHCHECK" in text, "HEALTHCHECK 없음"


def test_celery_dockerfile_is_multi_stage():
    text = (ROOT / "docker/celery.Dockerfile").read_text()
    assert text.count("FROM ") >= 2, "multi-stage build 아님"
    assert "USER app" in text, "비루트 사용자 없음"


def test_ci_has_coverage_gate():
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "--cov-fail-under=80" in text, "커버리지 게이트 없음"


def test_ci_has_bandit():
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "bandit" in text, "bandit 보안 스캔 없음"


def test_nginx_has_security_headers():
    text = (ROOT / "monitoring/nginx.conf").read_text()
    assert "X-Content-Type-Options" in text, "보안 헤더 없음"
    assert "client_max_body_size" in text, "body size 제한 없음"


def test_nginx_has_gzip():
    text = (ROOT / "monitoring/nginx.conf").read_text()
    assert "gzip on" in text, "gzip 미설정"


def test_prometheus_has_alert_rules():
    text = (ROOT / "monitoring/prometheus.yml").read_text()
    assert "alert_rules" in text, "alert rules 참조 없음"


def test_alert_rules_covers_key_scenarios():
    text = (ROOT / "monitoring/alert_rules.yml").read_text()
    for rule in ["HighErrorRate", "SlowP95", "BookingFailureSurge", "AntispoofOutage"]:
        assert rule in text, f"alert rule '{rule}' 없음"
