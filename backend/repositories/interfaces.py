"""Repository interface definitions — services depend on these, not SQL."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, List, Optional, Sequence, TypeVar

from comparison.result_models import ComparisonResult
from models.audit_session import AuditSession
from models.dealer_metadata import DealerMetadata
from models.investigation import InvestigationCase

if TYPE_CHECKING:
    from intelligence.models import IntelligenceFullResponse

T = TypeVar("T")


@dataclass
class PageResult(Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int


class DealerRepository(ABC):
    @abstractmethod
    def create(self, dealer: DealerMetadata) -> DealerMetadata: ...

    @abstractmethod
    def update(self, dealer: DealerMetadata) -> DealerMetadata: ...

    @abstractmethod
    def delete(self, dealer_id: str) -> None: ...

    @abstractmethod
    def get_by_id(self, dealer_id: str) -> Optional[DealerMetadata]: ...

    @abstractmethod
    def get_by_gstin_fy(self, gstin: str, financial_year: str) -> Optional[DealerMetadata]: ...


class AuditSessionRepository(ABC):
    @abstractmethod
    def create(self, session: AuditSession) -> AuditSession: ...

    @abstractmethod
    def update(self, session: AuditSession) -> AuditSession: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...

    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[AuditSession]: ...

    @abstractmethod
    def get_active_session_id(self) -> Optional[str]: ...

    @abstractmethod
    def set_active_session_id(self, session_id: str) -> None: ...

    @abstractmethod
    def clear_all(self) -> None: ...

    @abstractmethod
    def search(self, gstin: Optional[str] = None, financial_year: Optional[str] = None, limit: int = 50) -> List[AuditSession]: ...


class WorkbookRepository(ABC):
    @abstractmethod
    def cache_workbook(self, session_id: str, dataset_key: str, workbook_bytes: bytes) -> None: ...

    @abstractmethod
    def get_workbook(self, session_id: str, dataset_key: str) -> Optional[bytes]: ...

    @abstractmethod
    def delete_by_session(self, session_id: str) -> None: ...


class ComparisonRepository(ABC):
    @abstractmethod
    def save_result(self, result: ComparisonResult) -> None: ...

    @abstractmethod
    def get_result(self, session_id: str, comparison_id: Optional[str] = None) -> Optional[ComparisonResult]: ...

    @abstractmethod
    def list_results(self, session_id: str) -> List[ComparisonResult]: ...

    @abstractmethod
    def set_status(self, session_id: str, status: str) -> None: ...

    @abstractmethod
    def get_status(self, session_id: str) -> str: ...

    @abstractmethod
    def delete_by_session(self, session_id: str) -> None: ...

    @abstractmethod
    def search_records(
        self,
        session_id: str,
        result_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> PageResult: ...


class InvestigationCaseRepository(ABC):
    @abstractmethod
    def create(self, case: InvestigationCase) -> InvestigationCase: ...

    @abstractmethod
    def update(self, case: InvestigationCase) -> InvestigationCase: ...

    @abstractmethod
    def delete(self, session_id: str, case_id: str) -> None: ...

    @abstractmethod
    def get_by_id(self, session_id: str, case_id: str) -> Optional[InvestigationCase]: ...

    @abstractmethod
    def get_by_session(self, session_id: str) -> List[InvestigationCase]: ...

    @abstractmethod
    def save_many(self, session_id: str, cases: Sequence[InvestigationCase]) -> None: ...

    @abstractmethod
    def bulk_update(self, session_id: str, case_ids: List[str], updates: dict) -> int: ...

    @abstractmethod
    def search(
        self,
        session_id: str,
        *,
        status: Optional[str] = None,
        gstin: Optional[str] = None,
        month: Optional[str] = None,
        category: Optional[str] = None,
        high_risk_only: bool = False,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PageResult[InvestigationCase]: ...

    @abstractmethod
    def delete_by_session(self, session_id: str) -> None: ...


class AuditIntelligenceRepository(ABC):
    @abstractmethod
    def save(self, session_id: str, data: "IntelligenceFullResponse") -> None: ...

    @abstractmethod
    def get(self, session_id: str) -> Optional["IntelligenceFullResponse"]: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...


class AuditReportRepository(ABC):
    @abstractmethod
    def create(self, session_id: str, fmt: str, content: bytes, metadata: Optional[dict] = None) -> str: ...

    @abstractmethod
    def get_by_id(self, report_id: str) -> Optional[dict]: ...

    @abstractmethod
    def get_by_session(self, session_id: str) -> List[dict]: ...

    @abstractmethod
    def delete(self, report_id: str) -> None: ...


@dataclass
class RepositoryBundle:
    dealer: DealerRepository
    audit_session: AuditSessionRepository
    workbook: WorkbookRepository
    comparison: ComparisonRepository
    investigation: InvestigationCaseRepository
    intelligence: AuditIntelligenceRepository
    audit_report: AuditReportRepository
