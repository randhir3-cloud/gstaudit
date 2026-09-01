"""Tests for platform operations / system monitor API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_system_health_public_when_auth_disabled():
    res = client.get("/api/system/health")
    assert res.status_code == 200
    body = res.json()
    assert "status" in body
    assert "uptime_seconds" in body
    assert "version" in body


def test_system_metrics_endpoint():
    res = client.get("/api/system/metrics")
    assert res.status_code == 200
    body = res.json()
    assert "database" in body
    assert "jobs" in body
    assert "audit_sessions" in body
    assert "users" in body
    assert "performance" in body
    assert "storage" in body
    assert "backup" in body


def test_system_version_endpoint():
    res = client.get("/api/system/version")
    assert res.status_code == 200
    body = res.json()
    assert body["service"] == "GAIS"
    assert "version" in body
    assert "build_id" in body


def test_system_logs_search():
    res = client.get("/api/system/logs?limit=10")
    assert res.status_code == 200
    body = res.json()
    assert "logs" in body
    assert isinstance(body["logs"], list)


def test_system_jobs_endpoint():
    res = client.get("/api/system/jobs")
    assert res.status_code == 200
    body = res.json()
    assert "jobs" in body
    assert "summary" in body
