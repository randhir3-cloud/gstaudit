"""Case management workflow schema — audit lifecycle tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_case_management"
down_revision: Union[str, None] = "003_security"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_cases",
        sa.Column("audit_case_id", sa.String(64), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("audit_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_number", sa.String(64), server_default=""),
        sa.Column("master_case_id", sa.String(64), server_default="", index=True),
        sa.Column("invoice_number", sa.String(128), server_default=""),
        sa.Column("normalized_invoice", sa.String(128), server_default="", index=True),
        sa.Column("supplier_gstin", sa.String(15), server_default="", index=True),
        sa.Column("workflow_status", sa.String(64), server_default="Draft", index=True),
        sa.Column("priority", sa.String(16), server_default="Medium"),
        sa.Column("risk_score", sa.Integer, server_default="0"),
        sa.Column("assigned_officer", sa.String(128), server_default="", index=True),
        sa.Column("assigned_supervisor", sa.String(128), server_default=""),
        sa.Column("due_date", sa.String(32), server_default=""),
        sa.Column("case_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_audit_cases_session_status", "audit_cases", ["session_id", "workflow_status"])

    op.create_table(
        "case_assignments",
        sa.Column("assignment_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("assignment_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_notices",
        sa.Column("notice_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("notice_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "case_documents",
        sa.Column("document_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("document_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "case_comments",
        sa.Column("comment_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("comment_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "case_timelines",
        sa.Column("entry_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("timeline_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), index=True),
    )

    op.create_table(
        "dealer_responses",
        sa.Column("response_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("response_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "workflow_history",
        sa.Column("history_id", sa.String(64), primary_key=True),
        sa.Column("audit_case_id", sa.String(64), sa.ForeignKey("audit_cases.audit_case_id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("from_status", sa.String(64), server_default=""),
        sa.Column("to_status", sa.String(64), server_default=""),
        sa.Column("history_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("workflow_history")
    op.drop_table("dealer_responses")
    op.drop_table("case_timelines")
    op.drop_table("case_comments")
    op.drop_table("case_documents")
    op.drop_table("audit_notices")
    op.drop_table("case_assignments")
    op.drop_table("audit_cases")
