"""In-memory repository implementations — default provider."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Sequence

from comparison.result_models import ComparisonRecord, ComparisonResult
from intelligence.models import IntelligenceFullResponse
from models.audit_session import AuditSession
from models.dealer_metadata import DealerMetadata
from models.investigation import InvestigationCase

from repositories.interfaces import (
    AuditIntelligenceRepository,
    AuditReportRepository,
    AuditSessionRepository,
    ComparisonRepository,
    DealerRepository,
    InvestigationCaseRepository,
    PageResult,
    WorkbookRepository,
)


class MemoryDealerRepository(DealerRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, DealerMetadata] = {}
        self._by_gstin_fy: Dict[str, str] = {}

    def _key(self, gstin: str, fy: str) -> str:
        return f"{gstin.upper()}:{fy.strip()}"

    def create(self, dealer: DealerMetadata) -> DealerMetadata:
        dealer.ensure_id()
        self._by_id[dealer.id] = dealer
        self._by_gstin_fy[self._key(dealer.gstin, dealer.financial_year)] = dealer.id
        return dealer

    def update(self, dealer: DealerMetadata) -> DealerMetadata:
        return self.create(dealer)

    def delete(self, dealer_id: str) -> None:
        dealer = self._by_id.pop(dealer_id, None)
        if dealer:
            self._by_gstin_fy.pop(self._key(dealer.gstin, dealer.financial_year), None)

    def get_by_id(self, dealer_id: str) -> Optional[DealerMetadata]:
        return self._by_id.get(dealer_id)

    def get_by_gstin_fy(self, gstin: str, financial_year: str) -> Optional[DealerMetadata]:
        did = self._by_gstin_fy.get(self._key(gstin, financial_year))
        return self._by_id.get(did) if did else None


class MemoryAuditSessionRepository(AuditSessionRepository):
    def __init__(self, dealer_repo: MemoryDealerRepository) -> None:
        self._dealer_repo = dealer_repo
        self._sessions: Dict[str, AuditSession] = {}
        self._active_session_id: Optional[str] = None

    def create(self, session: AuditSession) -> AuditSession:
        if session.dealer and session.dealer.gstin:
            existing = self._dealer_repo.get_by_gstin_fy(session.dealer.gstin, session.dealer.financial_year)
            if existing:
                session.dealer.id = existing.id
            self._dealer_repo.create(session.dealer)
        self._sessions[session.session_id] = session
        self.set_active_session_id(session.session_id)
        return session

    def update(self, session: AuditSession) -> AuditSession:
        return self.create(session)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        if self._active_session_id == session_id:
            self._active_session_id = None

    def get_by_id(self, session_id: str) -> Optional[AuditSession]:
        return self._sessions.get(session_id)

    def get_active_session_id(self) -> Optional[str]:
        return self._active_session_id

    def set_active_session_id(self, session_id: str) -> None:
        self._active_session_id = session_id

    def clear_all(self) -> None:
        self._sessions.clear()
        self._active_session_id = None

    def search(self, gstin: Optional[str] = None, financial_year: Optional[str] = None, limit: int = 50) -> List[AuditSession]:
        items = list(self._sessions.values())
        if gstin:
            items = [s for s in items if s.dealer.gstin.upper() == gstin.upper()]
        if financial_year:
            items = [s for s in items if s.financial_year == financial_year]
        return items[:limit]


class MemoryWorkbookRepository(WorkbookRepository):
    def __init__(self) -> None:
        self._workbooks: Dict[str, Dict[str, bytes]] = {}

    def cache_workbook(self, session_id: str, dataset_key: str, workbook_bytes: bytes) -> None:
        self._workbooks.setdefault(session_id, {})[dataset_key] = workbook_bytes

    def get_workbook(self, session_id: str, dataset_key: str) -> Optional[bytes]:
        return self._workbooks.get(session_id, {}).get(dataset_key)

    def delete_by_session(self, session_id: str) -> None:
        self._workbooks.pop(session_id, None)


class MemoryComparisonRepository(ComparisonRepository):
    def __init__(self) -> None:
        self._results: Dict[str, Dict[str, ComparisonResult]] = {}
        self._status: Dict[str, str] = {}

    def _session_store(self, session_id: str) -> Dict[str, ComparisonResult]:
        return self._results.setdefault(session_id, {})

    def save_result(self, result: ComparisonResult) -> None:
        self._session_store(result.session_id)[result.comparison_id] = result
        self._status[result.session_id] = result.status

    def get_result(self, session_id: str, comparison_id: Optional[str] = None) -> Optional[ComparisonResult]:
        store = self._session_store(session_id)
        if not store:
            return None
        if comparison_id:
            return store.get(comparison_id)
        return next(iter(reversed(store.values())), None)

    def list_results(self, session_id: str) -> List[ComparisonResult]:
        return list(self._session_store(session_id).values())

    def set_status(self, session_id: str, status: str) -> None:
        self._status[session_id] = status

    def get_status(self, session_id: str) -> str:
        return self._status.get(session_id, "not_started")

    def delete_by_session(self, session_id: str) -> None:
        self._results.pop(session_id, None)
        self._status.pop(session_id, None)

    def search_records(
        self,
        session_id: str,
        result_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> PageResult:
        store = self._session_store(session_id)
        records: List[ComparisonRecord] = []
        for result in store.values():
            records.extend(result.records)
        if result_type:
            records = [r for r in records if r.result_type == result_type]
        total = len(records)
        page = records[offset : offset + limit]
        return PageResult(items=page, total=total, offset=offset, limit=limit)


class MemoryInvestigationCaseRepository(InvestigationCaseRepository):
    def __init__(self) -> None:
        self._cases: Dict[str, Dict[str, InvestigationCase]] = {}

    def _store(self, session_id: str) -> Dict[str, InvestigationCase]:
        return self._cases.setdefault(session_id, {})

    def create(self, case: InvestigationCase) -> InvestigationCase:
        self._store(case.session_id)[case.case_id] = case
        return case

    def update(self, case: InvestigationCase) -> InvestigationCase:
        return self.create(case)

    def delete(self, session_id: str, case_id: str) -> None:
        self._store(session_id).pop(case_id, None)

    def get_by_id(self, session_id: str, case_id: str) -> Optional[InvestigationCase]:
        return self._store(session_id).get(case_id)

    def get_by_session(self, session_id: str) -> List[InvestigationCase]:
        return list(self._store(session_id).values())

    def save_many(self, session_id: str, cases: Sequence[InvestigationCase]) -> None:
        store = self._store(session_id)
        for case in cases:
            store[case.case_id] = case

    def bulk_update(self, session_id: str, case_ids: List[str], updates: dict) -> int:
        count = 0
        store = self._store(session_id)
        for cid in case_ids:
            case = store.get(cid)
            if not case:
                continue
            data = case.model_dump()
            data.update({k: v for k, v in updates.items() if v is not None})
            store[cid] = InvestigationCase.model_validate(data)
            count += 1
        return count

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
    ) -> PageResult[InvestigationCase]:
        items = list(self._store(session_id).values())
        if status:
            items = [c for c in items if c.status == status]
        if gstin:
            g = gstin.upper()
            items = [c for c in items if g in (c.supplier_gstin or "").upper() or g in (c.recipient_gstin or "").upper()]
        if month:
            items = [c for c in items if month in (c.source_period or "")]
        if category and category != "ALL":
            if category == "HIGH_RISK":
                items = [c for c in items if c.priority in ("High", "Critical")]
            else:
                items = [c for c in items if c.result_type == category or c.comparison_result == category]
        if high_risk_only:
            items = [c for c in items if c.risk_score >= 70]
        if search:
            q = search.lower()
            items = [
                c for c in items
                if q in (c.invoice_number or "").lower()
                or q in (c.normalized_invoice or "").lower()
                or q in (c.case_number or "").lower()
                or q in (c.supplier_gstin or "").lower()
            ]
        total = len(items)
        return PageResult(items=items[offset : offset + limit], total=total, offset=offset, limit=limit)

    def delete_by_session(self, session_id: str) -> None:
        self._cases.pop(session_id, None)


class MemoryAuditIntelligenceRepository(AuditIntelligenceRepository):
    def __init__(self) -> None:
        self._cache: Dict[str, IntelligenceFullResponse] = {}

    def save(self, session_id: str, data: IntelligenceFullResponse) -> None:
        self._cache[session_id] = data

    def get(self, session_id: str) -> Optional[IntelligenceFullResponse]:
        return self._cache.get(session_id)

    def delete(self, session_id: str) -> None:
        self._cache.pop(session_id, None)


class MemoryAuditReportRepository(AuditReportRepository):
    def __init__(self) -> None:
        self._reports: Dict[str, dict] = {}

    def create(self, session_id: str, fmt: str, content: bytes, metadata: Optional[dict] = None) -> str:
        rid = str(uuid.uuid4())
        self._reports[rid] = {
            "id": rid,
            "session_id": session_id,
            "format": fmt,
            "content": content,
            "metadata": metadata or {},
        }
        return rid

    def get_by_id(self, report_id: str) -> Optional[dict]:
        return self._reports.get(report_id)

    def get_by_session(self, session_id: str) -> List[dict]:
        return [r for r in self._reports.values() if r["session_id"] == session_id]

    def delete(self, report_id: str) -> None:
        self._reports.pop(report_id, None)
