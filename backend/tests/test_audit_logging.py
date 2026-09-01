"""Audit logging tests."""

from __future__ import annotations

import pytest

from models.security import User
from repositories.security_repository import get_security_repository, reset_security_repository
from services.audit_log_service import list_recent_audit_logs, log_audit_event
from services.auth_service import bootstrap_security, login


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "false")
    from config.settings import get_settings

    get_settings.cache_clear()
    reset_security_repository()
    get_security_repository().clear_all()
    bootstrap_security()
    yield
    reset_security_repository()
    get_settings.cache_clear()


class TestAuditLogging:
    def test_login_creates_audit_log(self):
        login("admin", "Admin@123456!", ip_address="127.0.0.1", user_agent="pytest")
        logs = list_recent_audit_logs(limit=5)
        assert any(l.action == "login" for l in logs)

    def test_manual_audit_entry(self):
        user = User(user_id="u1", username="tester", permissions=["view_dashboard"])
        log_audit_event(user, "upload", gstin="03AABCU9603R1ZX", session_id="session_test", ip_address="10.0.0.1")
        logs = list_recent_audit_logs(limit=1)
        assert logs[0].action == "upload"
        assert logs[0].gstin == "03AABCU9603R1ZX"
