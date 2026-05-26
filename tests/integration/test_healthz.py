import pytest


@pytest.mark.django_db
def test_healthz_returns_200(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}