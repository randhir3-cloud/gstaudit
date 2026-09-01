"""Pytest configuration — disable auth for unit tests by default."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def disable_auth_for_tests(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    from config.settings import get_settings
    from repositories.security_repository import reset_security_repository

    get_settings.cache_clear()
    reset_security_repository()
    yield
    get_settings.cache_clear()
    reset_security_repository()
