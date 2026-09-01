"""Repository factory — selects memory or postgres implementation via config."""

from __future__ import annotations

from functools import lru_cache

from config.settings import get_settings
from repositories.interfaces import RepositoryBundle
from repositories.memory import (
    MemoryAuditIntelligenceRepository,
    MemoryAuditReportRepository,
    MemoryAuditSessionRepository,
    MemoryComparisonRepository,
    MemoryDealerRepository,
    MemoryInvestigationCaseRepository,
    MemoryWorkbookRepository,
)
from repositories.postgres import (
    PostgresAuditIntelligenceRepository,
    PostgresAuditReportRepository,
    PostgresAuditSessionRepository,
    PostgresComparisonRepository,
    PostgresDealerRepository,
    PostgresInvestigationCaseRepository,
    PostgresWorkbookRepository,
)


def _build_memory_bundle() -> RepositoryBundle:
    dealer = MemoryDealerRepository()
    return RepositoryBundle(
        dealer=dealer,
        audit_session=MemoryAuditSessionRepository(dealer),
        workbook=MemoryWorkbookRepository(),
        comparison=MemoryComparisonRepository(),
        investigation=MemoryInvestigationCaseRepository(),
        intelligence=MemoryAuditIntelligenceRepository(),
        audit_report=MemoryAuditReportRepository(),
    )


def _build_postgres_bundle() -> RepositoryBundle:
    dealer = PostgresDealerRepository()
    return RepositoryBundle(
        dealer=dealer,
        audit_session=PostgresAuditSessionRepository(dealer),
        workbook=PostgresWorkbookRepository(),
        comparison=PostgresComparisonRepository(),
        investigation=PostgresInvestigationCaseRepository(),
        intelligence=PostgresAuditIntelligenceRepository(),
        audit_report=PostgresAuditReportRepository(),
    )


@lru_cache(maxsize=1)
def get_repositories() -> RepositoryBundle:
    settings = get_settings()
    if settings.is_postgres:
        return _build_postgres_bundle()
    return _build_memory_bundle()


def reset_repositories() -> None:
    """Clear cached bundle (tests)."""
    get_repositories.cache_clear()
