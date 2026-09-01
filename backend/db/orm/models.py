"""SQLAlchemy ORM models — normalized GAIS persistence schema."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class DealerORM(Base):
    __tablename__ = "dealers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    gstin: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(512), default="")
    trade_name: Mapped[str] = mapped_column(String(512), default="")
    financial_year: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    tax_period: Mapped[str] = mapped_column(String(32), default="")
    arn: Mapped[str] = mapped_column(String(64), default="")
    arn_date: Mapped[str] = mapped_column(String(32), default="")
    download_date: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    sessions: Mapped[list["AuditSessionORM"]] = relationship(back_populates="dealer")

    __table_args__ = (
        UniqueConstraint("gstin", "financial_year", name="uq_dealers_gstin_fy"),
        Index("ix_dealers_gstin_fy", "gstin", "financial_year"),
    )


class AuditSessionORM(Base):
    __tablename__ = "audit_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dealer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dealers.id"), nullable=True)
    financial_year: Mapped[str] = mapped_column(String(16), default="", index=True)
    tax_period: Mapped[str] = mapped_column(String(32), default="")
    audit_status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    session_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    dealer: Mapped[Optional[DealerORM]] = relationship(back_populates="sessions")
    uploaded_files: Mapped[list["UploadedFileORM"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    merged_datasets: Mapped[list["MergedDatasetORM"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    comparison_runs: Mapped[list["ComparisonRunORM"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    investigation_cases: Mapped[list["InvestigationCaseORM"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    audit_reports: Mapped[list["AuditReportORM"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    intelligence_results: Mapped[list["IntelligenceResultORM"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_audit_sessions_fy_status", "financial_year", "audit_status"),)


class UploadedFileORM(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    dataset_key: Mapped[str] = mapped_column(String(32), index=True)
    filename: Mapped[str] = mapped_column(String(512), default="")
    month: Mapped[str] = mapped_column(String(16), default="", index=True)
    rows: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[AuditSessionORM] = relationship(back_populates="uploaded_files")

    __table_args__ = (Index("ix_uploaded_files_session_dataset", "session_id", "dataset_key"),)


class MergedDatasetORM(Base):
    __tablename__ = "merged_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    dataset_key: Mapped[str] = mapped_column(String(32), index=True)
    workbook_bytes: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    merged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[AuditSessionORM] = relationship(back_populates="merged_datasets")

    __table_args__ = (
        UniqueConstraint("session_id", "dataset_key", name="uq_merged_datasets_session_dataset"),
        Index("ix_merged_datasets_session", "session_id"),
    )


class ComparisonRunORM(Base):
    __tablename__ = "comparison_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    comparison_id: Mapped[str] = mapped_column(String(64), default="gstr1_ewb_outward", index=True)
    status: Mapped[str] = mapped_column(String(32), default="not_started", index=True)
    summary_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[AuditSessionORM] = relationship(back_populates="comparison_runs")
    results: Mapped[list["ComparisonResultORM"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    observations: Mapped[list["AuditObservationORM"]] = relationship(back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("session_id", "comparison_id", name="uq_comparison_runs_session_pair"),
        Index("ix_comparison_runs_session_status", "session_id", "status"),
    )


class ComparisonResultORM(Base):
    __tablename__ = "comparison_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("comparison_runs.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    result_type: Mapped[str] = mapped_column(String(64), index=True)
    invoice_number: Mapped[str] = mapped_column(String(128), default="", index=True)
    normalized_invoice: Mapped[str] = mapped_column(String(128), default="", index=True)
    gstin_gstr1: Mapped[str] = mapped_column(String(15), default="", index=True)
    gstin_eway: Mapped[str] = mapped_column(String(15), default="", index=True)
    source_period: Mapped[str] = mapped_column(String(16), default="", index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    record_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    run: Mapped[ComparisonRunORM] = relationship(back_populates="results")

    __table_args__ = (
        Index("ix_comparison_results_session_type", "session_id", "result_type"),
        Index("ix_comparison_results_invoice", "session_id", "normalized_invoice"),
    )


class AuditObservationORM(Base):
    __tablename__ = "audit_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("comparison_runs.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(128), default="", index=True)
    result_type: Mapped[str] = mapped_column(String(64), default="")
    observation: Mapped[str] = mapped_column(Text, default="")
    possible_reasons: Mapped[list] = mapped_column(JSONB, default=list)
    officer_action: Mapped[str] = mapped_column(Text, default="")

    run: Mapped[ComparisonRunORM] = relationship(back_populates="observations")

    __table_args__ = (Index("ix_audit_observations_session", "session_id"),)


class InvestigationCaseORM(Base):
    __tablename__ = "investigation_cases"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    case_number: Mapped[str] = mapped_column(String(64), default="")
    result_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    invoice_number: Mapped[str] = mapped_column(String(128), default="", index=True)
    normalized_invoice: Mapped[str] = mapped_column(String(128), default="", index=True)
    supplier_gstin: Mapped[str] = mapped_column(String(15), default="", index=True)
    recipient_gstin: Mapped[str] = mapped_column(String(15), default="")
    invoice_date: Mapped[str] = mapped_column(String(32), default="")
    invoice_value: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_value: Mapped[float] = mapped_column(Float, default=0.0)
    comparison_result: Mapped[str] = mapped_column(String(64), default="")
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    source_period: Mapped[str] = mapped_column(String(16), default="", index=True)
    status: Mapped[str] = mapped_column(String(64), default="Pending", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="Medium", index=True)
    priority_score: Mapped[int] = mapped_column(Integer, default=0)
    officer_remarks: Mapped[str] = mapped_column(Text, default="")
    case_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    session: Mapped[AuditSessionORM] = relationship(back_populates="investigation_cases")

    __table_args__ = (
        Index("ix_investigation_cases_session_status", "session_id", "status"),
        Index("ix_investigation_cases_session_priority", "session_id", "priority"),
        Index("ix_investigation_cases_gstin", "session_id", "supplier_gstin"),
    )


class AuditReportORM(Base):
    __tablename__ = "audit_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), index=True)
    format: Mapped[str] = mapped_column(String(16), default="pdf")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    report_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    content: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[AuditSessionORM] = relationship(back_populates="audit_reports")


class IntelligenceResultORM(Base):
    __tablename__ = "intelligence_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[AuditSessionORM] = relationship(back_populates="intelligence_results")


class SystemSettingORM(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class JobORM(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    job_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    result_ref: Mapped[dict] = mapped_column(JSONB, default=dict)
    checkpoint: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str] = mapped_column(Text, default="")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    progress_stage: Mapped[str] = mapped_column(String(128), default="")
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    rows_total: Mapped[int] = mapped_column(Integer, default=0)
    eta_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    logs: Mapped[list["JobLogORM"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    progress_history: Mapped[list["JobProgressORM"]] = relationship(back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_session_status", "session_id", "status"),
        Index("ix_jobs_type_status", "job_type", "status"),
    )


class JobLogORM(Base):
    __tablename__ = "job_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True)
    level: Mapped[str] = mapped_column(String(16), default="info")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job: Mapped[JobORM] = relationship(back_populates="logs")


class JobProgressORM(Base):
    __tablename__ = "job_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True)
    percent: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String(128), default="")
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    rows_total: Mapped[int] = mapped_column(Integer, default=0)
    eta_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job: Mapped[JobORM] = relationship(back_populates="progress_history")


class RoleORM(Base):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class RolePermissionORM(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(String(64), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)
    permission_code: Mapped[str] = mapped_column(String(64), primary_key=True)


class UserORM(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(256), default="")
    full_name: Mapped[str] = mapped_column(String(256), default="")
    department: Mapped[str] = mapped_column(String(128), default="")
    office: Mapped[str] = mapped_column(String(128), default="")
    designation: Mapped[str] = mapped_column(String(128), default="")
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class UserRoleORM(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(64), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)


class UserPasswordHistoryORM(Base):
    __tablename__ = "user_password_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UserSessionORM(Base):
    __tablename__ = "user_sessions"

    session_token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(128), index=True)
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(64), default="")
    action: Mapped[str] = mapped_column(String(64), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), default="")
    resource_id: Mapped[str] = mapped_column(String(128), default="")
    dealer_name: Mapped[str] = mapped_column(String(256), default="")
    gstin: Mapped[str] = mapped_column(String(15), default="")
    session_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(String(32), default="success")
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (Index("ix_audit_logs_action_time", "action", "timestamp"),)


class DepartmentSettingORM(Base):
    __tablename__ = "department_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
