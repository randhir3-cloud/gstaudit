"""Alembic migration — security schema (users, roles, audit logs, sessions)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_security"
down_revision: Union[str, None] = "002_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), server_default=""),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("is_system", sa.Boolean, server_default=sa.text("false")),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(64), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_code", sa.String(64), primary_key=True),
    )

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(256), server_default=""),
        sa.Column("full_name", sa.String(256), server_default=""),
        sa.Column("department", sa.String(128), server_default=""),
        sa.Column("office", sa.String(128), server_default=""),
        sa.Column("designation", sa.String(128), server_default=""),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("must_change_password", sa.Boolean, server_default=sa.text("false")),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(64), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_password_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_user_password_history_user_id", "user_password_history", ["user_id"])

    op.create_table(
        "user_sessions",
        sa.Column("session_token", sa.String(128), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(128), nullable=False),
        sa.Column("ip_address", sa.String(64), server_default=""),
        sa.Column("user_agent", sa.Text, server_default=""),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_refresh", "user_sessions", ["refresh_token_hash"])
    op.create_index("ix_user_sessions_active", "user_sessions", ["is_active"])

    op.create_table(
        "audit_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("username", sa.String(64), server_default=""),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), server_default=""),
        sa.Column("resource_id", sa.String(128), server_default=""),
        sa.Column("dealer_name", sa.String(256), server_default=""),
        sa.Column("gstin", sa.String(15), server_default=""),
        sa.Column("session_id", sa.String(64), server_default=""),
        sa.Column("ip_address", sa.String(64), server_default=""),
        sa.Column("user_agent", sa.Text, server_default=""),
        sa.Column("result", sa.String(32), server_default="success"),
        sa.Column("details", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_session_id", "audit_logs", ["session_id"])
    op.create_index("ix_audit_logs_action_time", "audit_logs", ["action", "timestamp"])

    op.create_table(
        "department_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("department_settings")
    op.drop_table("audit_logs")
    op.drop_table("user_sessions")
    op.drop_table("user_password_history")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("roles")
