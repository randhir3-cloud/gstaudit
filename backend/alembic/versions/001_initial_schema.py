"""Initial GAIS schema

Revision ID: 001_initial
Revises:
Create Date: 2026-07-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dealers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gstin", sa.String(15), nullable=False),
        sa.Column("legal_name", sa.String(512), server_default=""),
        sa.Column("trade_name", sa.String(512), server_default=""),
        sa.Column("financial_year", sa.String(16), nullable=False),
        sa.Column("tax_period", sa.String(32), server_default=""),
        sa.Column("arn", sa.String(64), server_default=""),
        sa.Column("arn_date", sa.String(32), server_default=""),
        sa.Column("download_date", sa.String(32), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("gstin", "financial_year", name="uq_dealers_gstin_fy"),
    )
    op.create_index("ix_dealers_gstin", "dealers", ["gstin"])
    op.create_index("ix_dealers_financial_year", "dealers", ["financial_year"])
    op.create_index("ix_dealers_gstin_fy", "dealers", ["gstin", "financial_year"])

    op.create_table(
        "audit_sessions",
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column("dealer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dealers.id"), nullable=True),
        sa.Column("financial_year", sa.String(16), server_default=""),
        sa.Column("tax_period", sa.String(32), server_default=""),
        sa.Column("audit_status", sa.String(32), server_default="draft"),
        sa.Column("session_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_sessions_financial_year", "audit_sessions", ["financial_year"])
    op.create_index("ix_audit_sessions_audit_status", "audit_sessions", ["audit_status"])
    op.create_index("ix_audit_sessions_is_active", "audit_sessions", ["is_active"])
    op.create_index("ix_audit_sessions_fy_status", "audit_sessions", ["financial_year", "audit_status"])

    op.create_table(
        "uploaded_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("dataset_key", sa.String(32), nullable=False),
        sa.Column("filename", sa.String(512), server_default=""),
        sa.Column("month", sa.String(16), server_default=""),
        sa.Column("rows", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(32), server_default="uploaded"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_uploaded_files_session_id", "uploaded_files", ["session_id"])
    op.create_index("ix_uploaded_files_dataset_key", "uploaded_files", ["dataset_key"])
    op.create_index("ix_uploaded_files_month", "uploaded_files", ["month"])
    op.create_index("ix_uploaded_files_session_dataset", "uploaded_files", ["session_id", "dataset_key"])

    op.create_table(
        "merged_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("dataset_key", sa.String(32), nullable=False),
        sa.Column("workbook_bytes", sa.LargeBinary, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("row_count", sa.Integer, server_default="0"),
        sa.Column("merged_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "dataset_key", name="uq_merged_datasets_session_dataset"),
    )
    op.create_index("ix_merged_datasets_session_id", "merged_datasets", ["session_id"])
    op.create_index("ix_merged_datasets_dataset_key", "merged_datasets", ["dataset_key"])

    op.create_table(
        "comparison_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("comparison_id", sa.String(64), server_default="gstr1_ewb_outward"),
        sa.Column("status", sa.String(32), server_default="not_started"),
        sa.Column("summary_json", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("session_id", "comparison_id", name="uq_comparison_runs_session_pair"),
    )
    op.create_index("ix_comparison_runs_session_id", "comparison_runs", ["session_id"])
    op.create_index("ix_comparison_runs_comparison_id", "comparison_runs", ["comparison_id"])
    op.create_index("ix_comparison_runs_status", "comparison_runs", ["status"])
    op.create_index("ix_comparison_runs_session_status", "comparison_runs", ["session_id", "status"])

    op.create_table(
        "comparison_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comparison_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("result_type", sa.String(64), nullable=False),
        sa.Column("invoice_number", sa.String(128), server_default=""),
        sa.Column("normalized_invoice", sa.String(128), server_default=""),
        sa.Column("gstin_gstr1", sa.String(15), server_default=""),
        sa.Column("gstin_eway", sa.String(15), server_default=""),
        sa.Column("source_period", sa.String(16), server_default=""),
        sa.Column("risk_score", sa.Integer, server_default="0"),
        sa.Column("record_json", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_comparison_results_run_id", "comparison_results", ["run_id"])
    op.create_index("ix_comparison_results_session_id", "comparison_results", ["session_id"])
    op.create_index("ix_comparison_results_result_type", "comparison_results", ["result_type"])
    op.create_index("ix_comparison_results_invoice_number", "comparison_results", ["invoice_number"])
    op.create_index("ix_comparison_results_normalized_invoice", "comparison_results", ["normalized_invoice"])
    op.create_index("ix_comparison_results_gstin_gstr1", "comparison_results", ["gstin_gstr1"])
    op.create_index("ix_comparison_results_gstin_eway", "comparison_results", ["gstin_eway"])
    op.create_index("ix_comparison_results_source_period", "comparison_results", ["source_period"])
    op.create_index("ix_comparison_results_risk_score", "comparison_results", ["risk_score"])
    op.create_index("ix_comparison_results_session_type", "comparison_results", ["session_id", "result_type"])
    op.create_index("ix_comparison_results_invoice", "comparison_results", ["session_id", "normalized_invoice"])

    op.create_table(
        "audit_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comparison_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_number", sa.String(128), server_default=""),
        sa.Column("result_type", sa.String(64), server_default=""),
        sa.Column("observation", sa.Text, server_default=""),
        sa.Column("possible_reasons", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("officer_action", sa.Text, server_default=""),
    )
    op.create_index("ix_audit_observations_run_id", "audit_observations", ["run_id"])
    op.create_index("ix_audit_observations_session_id", "audit_observations", ["session_id"])
    op.create_index("ix_audit_observations_invoice_number", "audit_observations", ["invoice_number"])

    op.create_table(
        "investigation_cases",
        sa.Column("case_id", sa.String(64), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_number", sa.String(64), server_default=""),
        sa.Column("result_type", sa.String(64), server_default=""),
        sa.Column("invoice_number", sa.String(128), server_default=""),
        sa.Column("normalized_invoice", sa.String(128), server_default=""),
        sa.Column("supplier_gstin", sa.String(15), server_default=""),
        sa.Column("recipient_gstin", sa.String(15), server_default=""),
        sa.Column("invoice_date", sa.String(32), server_default=""),
        sa.Column("invoice_value", sa.Float, server_default="0"),
        sa.Column("taxable_value", sa.Float, server_default="0"),
        sa.Column("comparison_result", sa.String(64), server_default=""),
        sa.Column("risk_score", sa.Integer, server_default="0"),
        sa.Column("source_period", sa.String(16), server_default=""),
        sa.Column("status", sa.String(64), server_default="Pending"),
        sa.Column("priority", sa.String(16), server_default="Medium"),
        sa.Column("priority_score", sa.Integer, server_default="0"),
        sa.Column("officer_remarks", sa.Text, server_default=""),
        sa.Column("case_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_investigation_cases_session_id", "investigation_cases", ["session_id"])
    op.create_index("ix_investigation_cases_result_type", "investigation_cases", ["result_type"])
    op.create_index("ix_investigation_cases_invoice_number", "investigation_cases", ["invoice_number"])
    op.create_index("ix_investigation_cases_normalized_invoice", "investigation_cases", ["normalized_invoice"])
    op.create_index("ix_investigation_cases_supplier_gstin", "investigation_cases", ["supplier_gstin"])
    op.create_index("ix_investigation_cases_source_period", "investigation_cases", ["source_period"])
    op.create_index("ix_investigation_cases_risk_score", "investigation_cases", ["risk_score"])
    op.create_index("ix_investigation_cases_status", "investigation_cases", ["status"])
    op.create_index("ix_investigation_cases_priority", "investigation_cases", ["priority"])
    op.create_index("ix_investigation_cases_session_status", "investigation_cases", ["session_id", "status"])
    op.create_index("ix_investigation_cases_session_priority", "investigation_cases", ["session_id", "priority"])
    op.create_index("ix_investigation_cases_gstin", "investigation_cases", ["session_id", "supplier_gstin"])

    op.create_table(
        "audit_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(16), server_default="pdf"),
        sa.Column("file_size", sa.BigInteger, server_default="0"),
        sa.Column("report_metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("content", sa.LargeBinary, nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_reports_session_id", "audit_reports", ["session_id"])

    op.create_table(
        "intelligence_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_intelligence_results_session_id", "intelligence_results", ["session_id"])

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("intelligence_results")
    op.drop_table("audit_reports")
    op.drop_table("investigation_cases")
    op.drop_table("audit_observations")
    op.drop_table("comparison_results")
    op.drop_table("comparison_runs")
    op.drop_table("merged_datasets")
    op.drop_table("uploaded_files")
    op.drop_table("audit_sessions")
    op.drop_table("dealers")
