"""Security service tests."""

from __future__ import annotations

import pytest

from auth.password import hash_password, validate_password, verify_password
from models.security import PasswordPolicy, UserCreateRequest, UserStatus
from repositories.security_repository import get_security_repository, reset_security_repository
from services.auth_service import bootstrap_security, login
from services.user_service import create_user, list_roles


@pytest.fixture(autouse=True)
def clean_security(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "false")
    from config.settings import get_settings

    get_settings.cache_clear()
    reset_security_repository()
    repo = get_security_repository()
    repo.clear_all()
    bootstrap_security()
    yield
    repo.clear_all()
    reset_security_repository()
    get_settings.cache_clear()


class TestAuthService:
    def test_login_success(self):
        result, refresh, csrf = login("admin", "Admin@123456!")
        assert result.access_token
        assert result.user.username == "admin"
        assert refresh
        assert csrf

    def test_login_invalid_password(self):
        with pytest.raises(ValueError):
            login("admin", "wrong-password")

    def test_password_policy(self):
        policy = PasswordPolicy(min_length=8, require_special=False)
        validate_password("Simple12", policy)
        with pytest.raises(ValueError):
            validate_password("short", policy)

    def test_roles_seeded(self):
        roles = list_roles()
        names = {r.name for r in roles}
        assert "administrator" in names
        assert "audit_officer" in names


class TestRBAC:
    def test_admin_has_manage_users(self):
        result, _, _ = login("admin", "Admin@123456!")
        assert "manage_users" in result.user.permissions

    def test_create_officer_user(self):
        admin_login, _, _ = login("admin", "Admin@123456!")
        officer = create_user(
            UserCreateRequest(username="officer1", password="Officer@123456", role_ids=["role_officer"]),
            admin_login.user,
        )
        assert officer.status == UserStatus.ACTIVE
        assert "run_comparison" in officer.permissions
        assert "manage_users" not in officer.permissions
