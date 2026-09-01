"""Plugin runtime context — services exposed to plugins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from comparison.registry import comparison_registry
from config.settings import Settings, get_settings
from repositories.factory import RepositoryBundle, get_repositories

if TYPE_CHECKING:
    from fastapi import FastAPI


@dataclass(frozen=True)
class PluginContext:
    """Stable platform API surface for plugins."""

    app: "FastAPI | None" = None

    @property
    def settings(self) -> Settings:
        return get_settings()

    @property
    def repositories(self) -> RepositoryBundle:
        return get_repositories()

    @property
    def comparisons(self):
        return comparison_registry

    def get_session(self, session_id: str | None = None):
        from services.audit_session_store import get_session

        return get_session(session_id)

    def upsert_session(self, session):
        from services.audit_session_store import upsert_session

        return upsert_session(session)

    def create_job(self, request):
        from services.job_service import create_job

        return create_job(request)

    def log_audit(self, user, action: str, **kwargs):
        from services.audit_log_service import log_audit_event

        return log_audit_event(user, action, **kwargs)

    def cache_workbook(self, session_id: str, dataset_key: str, data: bytes):
        from services.comparison_store import cache_workbook

        return cache_workbook(session_id, dataset_key, data)

    def get_workbook(self, session_id: str, dataset_key: str):
        from services.comparison_store import get_workbook

        return get_workbook(session_id, dataset_key)

    def build_dashboard(self, session):
        from services.dashboard_service import build_dashboard

        return build_dashboard(session)
