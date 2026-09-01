"""Pydantic ↔ ORM conversion helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from comparison.result_models import AuditObservation, ComparisonRecord, ComparisonResult, ComparisonSummary
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
from intelligence.models import IntelligenceFullResponse
from models.audit_session import AuditSession, UploadHistoryEntry
from models.dealer_metadata import DealerMetadata
from models.investigation import CaseAttachment, InvestigationCase


def dealer_to_orm(dealer: DealerMetadata) -> DealerORM:
    dealer.ensure_id()
    return DealerORM(
        id=uuid.UUID(dealer.id),
        gstin=dealer.gstin.upper(),
        legal_name=dealer.legal_name,
        trade_name=dealer.trade_name,
        financial_year=dealer.financial_year,
        tax_period=dealer.tax_period,
        arn=dealer.arn,
        arn_date=dealer.arn_date,
        download_date=dealer.download_date,
    )


def dealer_from_orm(row: DealerORM) -> DealerMetadata:
    return DealerMetadata(
        id=str(row.id),
        gstin=row.gstin,
        legal_name=row.legal_name,
        trade_name=row.trade_name,
        financial_year=row.financial_year,
        tax_period=row.tax_period,
        arn=row.arn,
        arn_date=row.arn_date,
        download_date=row.download_date,
    )


def session_to_orm(session: AuditSession, dealer_id: Optional[uuid.UUID] = None) -> AuditSessionORM:
    payload = session.model_dump(mode="json")
    payload.pop("session_id", None)
    return AuditSessionORM(
        session_id=session.session_id,
        dealer_id=dealer_id,
        financial_year=session.financial_year,
        tax_period=session.tax_period,
        audit_status=session.audit_status,
        session_payload=payload,
    )


def session_from_orm(row: AuditSessionORM, dealer: Optional[DealerMetadata] = None) -> AuditSession:
    data = dict(row.session_payload or {})
    data["session_id"] = row.session_id
    data["financial_year"] = row.financial_year or data.get("financial_year", "")
    data["tax_period"] = row.tax_period or data.get("tax_period", "")
    data["audit_status"] = row.audit_status or data.get("audit_status", "draft")
    if dealer:
        data["dealer"] = dealer.model_dump()
    return AuditSession.model_validate(data)


def upload_entries_from_session(session: AuditSession) -> List[UploadedFileORM]:
    rows: List[UploadedFileORM] = []
    for entry in session.upload_history:
        rows.append(
            UploadedFileORM(
                session_id=session.session_id,
                dataset_key=entry.dataset,
                filename=entry.filename,
                month=entry.month,
                rows=entry.rows,
                status=entry.status,
            )
        )
    return rows


def comparison_result_to_orm(result: ComparisonResult, run_id: uuid.UUID) -> tuple[ComparisonRunORM, List[ComparisonResultORM], List[AuditObservationORM]]:
    run = ComparisonRunORM(
        id=run_id,
        session_id=result.session_id,
        comparison_id=result.comparison_id,
        status=result.status,
        summary_json=result.summary.model_dump(mode="json"),
        completed_at=datetime.now(timezone.utc) if result.completed_at else None,
    )
    record_rows = []
    for rec in result.records:
        record_rows.append(
            ComparisonResultORM(
                run_id=run_id,
                session_id=result.session_id,
                result_type=rec.result_type,
                invoice_number=rec.invoice_number,
                normalized_invoice=rec.normalized_invoice,
                gstin_gstr1=rec.gstin_gstr1,
                gstin_eway=rec.gstin_eway,
                source_period=rec.source_period,
                risk_score=rec.risk_score,
                record_json=rec.model_dump(mode="json"),
            )
        )
    obs_rows = []
    for obs in result.observations:
        obs_rows.append(
            AuditObservationORM(
                run_id=run_id,
                session_id=result.session_id,
                invoice_number=obs.invoice_number,
                result_type=str(obs.result_type),
                observation=obs.observation,
                possible_reasons=obs.possible_reasons,
                officer_action=obs.officer_action,
            )
        )
    return run, record_rows, obs_rows


def comparison_result_from_orm(run: ComparisonRunORM, records: List[ComparisonResultORM], observations: List[AuditObservationORM]) -> ComparisonResult:
    summary = ComparisonSummary.model_validate(run.summary_json or {})
    rec_models = [ComparisonRecord.model_validate(r.record_json) for r in records]
    obs_models = [
        AuditObservation(
            invoice_number=o.invoice_number,
            result_type=o.result_type,
            observation=o.observation,
            possible_reasons=o.possible_reasons or [],
            officer_action=o.officer_action,
        )
        for o in observations
    ]
    completed = run.completed_at.isoformat() if run.completed_at else ""
    return ComparisonResult(
        session_id=run.session_id,
        comparison_id=run.comparison_id,
        status=run.status,
        summary=summary,
        records=rec_models,
        observations=obs_models,
        completed_at=completed,
    )


def case_to_orm(case: InvestigationCase) -> InvestigationCaseORM:
    payload = case.model_dump(mode="json")
    for key in (
        "case_id", "session_id", "case_number", "result_type", "invoice_number",
        "normalized_invoice", "supplier_gstin", "recipient_gstin", "invoice_date",
        "invoice_value", "taxable_value", "comparison_result", "risk_score",
        "source_period", "status", "priority", "priority_score", "officer_remarks",
    ):
        payload.pop(key, None)
    return InvestigationCaseORM(
        case_id=case.case_id,
        session_id=case.session_id,
        case_number=case.case_number,
        result_type=case.result_type,
        invoice_number=case.invoice_number,
        normalized_invoice=case.normalized_invoice,
        supplier_gstin=case.supplier_gstin,
        recipient_gstin=case.recipient_gstin,
        invoice_date=case.invoice_date,
        invoice_value=case.invoice_value,
        taxable_value=case.taxable_value,
        comparison_result=case.comparison_result,
        risk_score=case.risk_score,
        source_period=case.source_period,
        status=case.status,
        priority=case.priority,
        priority_score=case.priority_score,
        officer_remarks=case.officer_remarks,
        case_payload=payload,
    )


def case_from_orm(row: InvestigationCaseORM) -> InvestigationCase:
    data = dict(row.case_payload or {})
    data.update(
        case_id=row.case_id,
        session_id=row.session_id,
        case_number=row.case_number,
        result_type=row.result_type,
        invoice_number=row.invoice_number,
        normalized_invoice=row.normalized_invoice,
        supplier_gstin=row.supplier_gstin,
        recipient_gstin=row.recipient_gstin,
        invoice_date=row.invoice_date,
        invoice_value=row.invoice_value,
        taxable_value=row.taxable_value,
        comparison_result=row.comparison_result,
        risk_score=row.risk_score,
        source_period=row.source_period,
        status=row.status,
        priority=row.priority,
        priority_score=row.priority_score,
        officer_remarks=row.officer_remarks,
    )
    if "attachments" in data and isinstance(data["attachments"], dict):
        data["attachments"] = CaseAttachment.model_validate(data["attachments"])
    return InvestigationCase.model_validate(data)


def intelligence_to_orm(session_id: str, data: IntelligenceFullResponse) -> IntelligenceResultORM:
    return IntelligenceResultORM(session_id=session_id, payload=data.model_dump(mode="json"))


def intelligence_from_orm(row: IntelligenceResultORM) -> IntelligenceFullResponse:
    return IntelligenceFullResponse.model_validate(row.payload)


def report_to_orm(session_id: str, fmt: str, content: bytes, metadata: Optional[dict] = None) -> AuditReportORM:
    return AuditReportORM(
        session_id=session_id,
        format=fmt,
        content=content,
        file_size=len(content),
        report_metadata=metadata or {},
    )
