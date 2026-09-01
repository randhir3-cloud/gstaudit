"""PostgreSQL repository implementations via SQLAlchemy 2.x."""

from __future__ import annotations

import uuid
from typing import List, Optional, Sequence

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from comparison.result_models import ComparisonResult
from db.mappers import (
    case_from_orm,
    case_to_orm,
    comparison_result_from_orm,
    comparison_result_to_orm,
    dealer_from_orm,
    dealer_to_orm,
    intelligence_from_orm,
    intelligence_to_orm,
    report_to_orm,
    session_from_orm,
    session_to_orm,
    upload_entries_from_session,
)
from db.orm.models import (
    AuditObservationORM,
    AuditReportORM,
    AuditSessionORM,
    ComparisonResultORM,
    ComparisonRunORM,
    DealerORM,
    IntelligenceResultORM,
    InvestigationCaseORM,
    MergedDatasetORM,
    UploadedFileORM,
)
from db.session import session_scope
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


class PostgresDealerRepository(DealerRepository):
    def create(self, dealer: DealerMetadata) -> DealerMetadata:
        dealer.ensure_id()
        with session_scope() as db:
            existing = db.scalar(
                select(DealerORM).where(
                    DealerORM.gstin == dealer.gstin.upper(),
                    DealerORM.financial_year == dealer.financial_year,
                )
            )
            if existing:
                return dealer_from_orm(existing)
            row = dealer_to_orm(dealer)
            db.merge(row)
        return dealer

    def update(self, dealer: DealerMetadata) -> DealerMetadata:
        return self.create(dealer)

    def delete(self, dealer_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(DealerORM).where(DealerORM.id == uuid.UUID(dealer_id)))

    def get_by_id(self, dealer_id: str) -> Optional[DealerMetadata]:
        with session_scope() as db:
            row = db.get(DealerORM, uuid.UUID(dealer_id))
            return dealer_from_orm(row) if row else None

    def get_by_gstin_fy(self, gstin: str, financial_year: str) -> Optional[DealerMetadata]:
        with session_scope() as db:
            row = db.scalar(
                select(DealerORM).where(
                    DealerORM.gstin == gstin.upper(),
                    DealerORM.financial_year == financial_year,
                )
            )
            return dealer_from_orm(row) if row else None


class PostgresAuditSessionRepository(AuditSessionRepository):
    def __init__(self, dealer_repo: PostgresDealerRepository) -> None:
        self._dealer_repo = dealer_repo
        self._active_session_id: Optional[str] = None

    def create(self, session: AuditSession) -> AuditSession:
        dealer_id = None
        if session.dealer and session.dealer.gstin:
            saved = self._dealer_repo.create(session.dealer)
            dealer_id = uuid.UUID(saved.id)
        with session_scope() as db:
            row = session_to_orm(session, dealer_id=dealer_id)
            row.is_active = True
            db.merge(row)
            db.execute(update(AuditSessionORM).values(is_active=False).where(AuditSessionORM.session_id != session.session_id))
            db.execute(delete(UploadedFileORM).where(UploadedFileORM.session_id == session.session_id))
            for upload in upload_entries_from_session(session):
                db.add(upload)
        self._active_session_id = session.session_id
        return session

    def update(self, session: AuditSession) -> AuditSession:
        return self.create(session)

    def delete(self, session_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(AuditSessionORM).where(AuditSessionORM.session_id == session_id))
        if self._active_session_id == session_id:
            self._active_session_id = None

    def get_by_id(self, session_id: str) -> Optional[AuditSession]:
        with session_scope() as db:
            row = db.get(AuditSessionORM, session_id)
            if not row:
                return None
            dealer = None
            if row.dealer_id:
                drow = db.get(DealerORM, row.dealer_id)
                if drow:
                    dealer = dealer_from_orm(drow)
            return session_from_orm(row, dealer)

    def get_active_session_id(self) -> Optional[str]:
        if self._active_session_id:
            return self._active_session_id
        with session_scope() as db:
            row = db.scalar(select(AuditSessionORM.session_id).where(AuditSessionORM.is_active.is_(True)).limit(1))
            self._active_session_id = row
            return row

    def set_active_session_id(self, session_id: str) -> None:
        self._active_session_id = session_id
        with session_scope() as db:
            db.execute(update(AuditSessionORM).values(is_active=False))
            db.execute(update(AuditSessionORM).where(AuditSessionORM.session_id == session_id).values(is_active=True))

    def clear_all(self) -> None:
        self._active_session_id = None
        with session_scope() as db:
            db.execute(delete(AuditSessionORM))

    def search(self, gstin: Optional[str] = None, financial_year: Optional[str] = None, limit: int = 50) -> List[AuditSession]:
        with session_scope() as db:
            stmt = select(AuditSessionORM)
            if gstin:
                stmt = stmt.join(DealerORM).where(DealerORM.gstin == gstin.upper())
            if financial_year:
                stmt = stmt.where(AuditSessionORM.financial_year == financial_year)
            rows = db.scalars(stmt.limit(limit)).all()
            out = []
            for row in rows:
                dealer = None
                if row.dealer_id:
                    drow = db.get(DealerORM, row.dealer_id)
                    if drow:
                        dealer = dealer_from_orm(drow)
                out.append(session_from_orm(row, dealer))
            return out


class PostgresWorkbookRepository(WorkbookRepository):
    def cache_workbook(self, session_id: str, dataset_key: str, workbook_bytes: bytes) -> None:
        with session_scope() as db:
            existing = db.scalar(
                select(MergedDatasetORM).where(
                    MergedDatasetORM.session_id == session_id,
                    MergedDatasetORM.dataset_key == dataset_key,
                )
            )
            if existing:
                existing.workbook_bytes = workbook_bytes
            else:
                db.add(MergedDatasetORM(session_id=session_id, dataset_key=dataset_key, workbook_bytes=workbook_bytes))

    def get_workbook(self, session_id: str, dataset_key: str) -> Optional[bytes]:
        with session_scope() as db:
            row = db.scalar(
                select(MergedDatasetORM).where(
                    MergedDatasetORM.session_id == session_id,
                    MergedDatasetORM.dataset_key == dataset_key,
                )
            )
            return row.workbook_bytes if row else None

    def delete_by_session(self, session_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(MergedDatasetORM).where(MergedDatasetORM.session_id == session_id))


class PostgresComparisonRepository(ComparisonRepository):
    def save_result(self, result: ComparisonResult) -> None:
        run_id = uuid.uuid4()
        run, records, observations = comparison_result_to_orm(result, run_id)
        with session_scope() as db:
            existing = db.scalar(
                select(ComparisonRunORM).where(
                    ComparisonRunORM.session_id == result.session_id,
                    ComparisonRunORM.comparison_id == result.comparison_id,
                )
            )
            if existing:
                run_id = existing.id
                db.execute(delete(ComparisonResultORM).where(ComparisonResultORM.run_id == run_id))
                db.execute(delete(AuditObservationORM).where(AuditObservationORM.run_id == run_id))
                run.id = run_id
                db.merge(run)
            else:
                db.add(run)
            for rec in records:
                rec.run_id = run_id
                db.add(rec)
            for obs in observations:
                obs.run_id = run_id
                db.add(obs)

    def get_result(self, session_id: str, comparison_id: Optional[str] = None) -> Optional[ComparisonResult]:
        with session_scope() as db:
            stmt = select(ComparisonRunORM).where(ComparisonRunORM.session_id == session_id)
            if comparison_id:
                stmt = stmt.where(ComparisonRunORM.comparison_id == comparison_id)
            else:
                stmt = stmt.order_by(ComparisonRunORM.completed_at.desc().nullslast())
            run = db.scalar(stmt.limit(1))
            if not run:
                return None
            records = db.scalars(select(ComparisonResultORM).where(ComparisonResultORM.run_id == run.id)).all()
            observations = db.scalars(select(AuditObservationORM).where(AuditObservationORM.run_id == run.id)).all()
            return comparison_result_from_orm(run, list(records), list(observations))

    def list_results(self, session_id: str) -> List[ComparisonResult]:
        with session_scope() as db:
            runs = db.scalars(
                select(ComparisonRunORM)
                .where(ComparisonRunORM.session_id == session_id)
                .order_by(ComparisonRunORM.completed_at.desc().nullslast())
            ).all()
            results: List[ComparisonResult] = []
            seen: set[str] = set()
            for run in runs:
                if run.comparison_id in seen:
                    continue
                seen.add(run.comparison_id)
                records = db.scalars(select(ComparisonResultORM).where(ComparisonResultORM.run_id == run.id)).all()
                observations = db.scalars(select(AuditObservationORM).where(AuditObservationORM.run_id == run.id)).all()
                results.append(comparison_result_from_orm(run, list(records), list(observations)))
            return results

    def set_status(self, session_id: str, status: str) -> None:
        with session_scope() as db:
            db.execute(
                update(ComparisonRunORM)
                .where(ComparisonRunORM.session_id == session_id)
                .values(status=status)
            )

    def get_status(self, session_id: str) -> str:
        with session_scope() as db:
            run = db.scalar(
                select(ComparisonRunORM.status)
                .where(ComparisonRunORM.session_id == session_id)
                .order_by(ComparisonRunORM.completed_at.desc().nullslast())
                .limit(1)
            )
            return run or "not_started"

    def delete_by_session(self, session_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(ComparisonRunORM).where(ComparisonRunORM.session_id == session_id))

    def search_records(
        self,
        session_id: str,
        result_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> PageResult:
        with session_scope() as db:
            stmt = select(ComparisonResultORM).where(ComparisonResultORM.session_id == session_id)
            if result_type:
                stmt = stmt.where(ComparisonResultORM.result_type == result_type)
            total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            rows = db.scalars(stmt.offset(offset).limit(limit)).all()
            from comparison.result_models import ComparisonRecord

            items = [ComparisonRecord.model_validate(r.record_json) for r in rows]
            return PageResult(items=items, total=int(total), offset=offset, limit=limit)


class PostgresInvestigationCaseRepository(InvestigationCaseRepository):
    def create(self, case: InvestigationCase) -> InvestigationCase:
        with session_scope() as db:
            db.merge(case_to_orm(case))
        return case

    def update(self, case: InvestigationCase) -> InvestigationCase:
        return self.create(case)

    def delete(self, session_id: str, case_id: str) -> None:
        with session_scope() as db:
            db.execute(
                delete(InvestigationCaseORM).where(
                    InvestigationCaseORM.session_id == session_id,
                    InvestigationCaseORM.case_id == case_id,
                )
            )

    def get_by_id(self, session_id: str, case_id: str) -> Optional[InvestigationCase]:
        with session_scope() as db:
            row = db.get(InvestigationCaseORM, case_id)
            if not row or row.session_id != session_id:
                return None
            return case_from_orm(row)

    def get_by_session(self, session_id: str) -> List[InvestigationCase]:
        with session_scope() as db:
            rows = db.scalars(select(InvestigationCaseORM).where(InvestigationCaseORM.session_id == session_id)).all()
            return [case_from_orm(r) for r in rows]

    def save_many(self, session_id: str, cases: Sequence[InvestigationCase]) -> None:
        with session_scope() as db:
            for case in cases:
                db.merge(case_to_orm(case))

    def bulk_update(self, session_id: str, case_ids: List[str], updates: dict) -> int:
        if not case_ids:
            return 0
        with session_scope() as db:
            values = {k: v for k, v in updates.items() if v is not None}
            if not values:
                return 0
            result = db.execute(
                update(InvestigationCaseORM)
                .where(
                    InvestigationCaseORM.session_id == session_id,
                    InvestigationCaseORM.case_id.in_(case_ids),
                )
                .values(**{k: v for k, v in values.items() if k in InvestigationCaseORM.__table__.columns})
            )
            return result.rowcount or 0

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
        with session_scope() as db:
            stmt = select(InvestigationCaseORM).where(InvestigationCaseORM.session_id == session_id)
            if status:
                stmt = stmt.where(InvestigationCaseORM.status == status)
            if gstin:
                g = gstin.upper()
                stmt = stmt.where(
                    or_(
                        InvestigationCaseORM.supplier_gstin.ilike(f"%{g}%"),
                        InvestigationCaseORM.recipient_gstin.ilike(f"%{g}%"),
                    )
                )
            if month:
                stmt = stmt.where(InvestigationCaseORM.source_period.ilike(f"%{month}%"))
            if category and category not in ("ALL", "HIGH_RISK"):
                stmt = stmt.where(
                    or_(
                        InvestigationCaseORM.result_type == category,
                        InvestigationCaseORM.comparison_result == category,
                    )
                )
            if category == "HIGH_RISK" or high_risk_only:
                stmt = stmt.where(InvestigationCaseORM.priority.in_(["High", "Critical"]))
            if search:
                q = f"%{search.lower()}%"
                stmt = stmt.where(
                    or_(
                        InvestigationCaseORM.invoice_number.ilike(q),
                        InvestigationCaseORM.normalized_invoice.ilike(q),
                        InvestigationCaseORM.case_number.ilike(q),
                        InvestigationCaseORM.supplier_gstin.ilike(q),
                    )
                )
            total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            rows = db.scalars(stmt.offset(offset).limit(limit)).all()
            return PageResult(items=[case_from_orm(r) for r in rows], total=int(total), offset=offset, limit=limit)

    def delete_by_session(self, session_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(InvestigationCaseORM).where(InvestigationCaseORM.session_id == session_id))


class PostgresAuditIntelligenceRepository(AuditIntelligenceRepository):
    def save(self, session_id: str, data: IntelligenceFullResponse) -> None:
        with session_scope() as db:
            db.merge(intelligence_to_orm(session_id, data))

    def get(self, session_id: str) -> Optional[IntelligenceFullResponse]:
        with session_scope() as db:
            row = db.scalar(select(IntelligenceResultORM).where(IntelligenceResultORM.session_id == session_id))
            return intelligence_from_orm(row) if row else None

    def delete(self, session_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(IntelligenceResultORM).where(IntelligenceResultORM.session_id == session_id))


class PostgresAuditReportRepository(AuditReportRepository):
    def create(self, session_id: str, fmt: str, content: bytes, metadata: Optional[dict] = None) -> str:
        row = report_to_orm(session_id, fmt, content, metadata)
        with session_scope() as db:
            db.add(row)
            db.flush()
            return str(row.id)

    def get_by_id(self, report_id: str) -> Optional[dict]:
        with session_scope() as db:
            row = db.get(AuditReportORM, uuid.UUID(report_id))
            if not row:
                return None
            return {
                "id": str(row.id),
                "session_id": row.session_id,
                "format": row.format,
                "content": row.content,
                "metadata": row.report_metadata,
            }

    def get_by_session(self, session_id: str) -> List[dict]:
        with session_scope() as db:
            rows = db.scalars(select(AuditReportORM).where(AuditReportORM.session_id == session_id)).all()
            return [
                {
                    "id": str(r.id),
                    "session_id": r.session_id,
                    "format": r.format,
                    "file_size": r.file_size,
                    "metadata": r.report_metadata,
                }
                for r in rows
            ]

    def delete(self, report_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(AuditReportORM).where(AuditReportORM.id == uuid.UUID(report_id)))
