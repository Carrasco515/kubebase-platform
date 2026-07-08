"""Smoke tests for the KubeBase Platform demo API.

Run from the app/ directory:  pytest -q
These are fast, dependency-light tests used by CI to catch regressions in the
endpoints the Kubernetes probes and Prometheus scraping rely on.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_returns_app_info():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "environment" in body


def test_health_is_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_exposes_only_non_secret_values():
    response = client.get("/config")
    assert response.status_code == 200
    assert set(response.json()) == {"app_name", "app_env", "greeting", "log_level"}


def test_metrics_exposes_prometheus_format():
    client.get("/health")  # generate at least one counted request
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "health_check_total" in response.text
