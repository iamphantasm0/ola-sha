"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

ORDER_STATUS_VALUES = (
    "IDLE",
    "CANCELLED",
    "FAILED",
    "SETTLED",
    "OFFRAMP_QUOTING",
    "OFFRAMP_COLLECTING_BANK",
    "OFFRAMP_AWAITING_DEPOSIT",
    "OFFRAMP_PROCESSING",
    "ONRAMP_QUOTING",
    "ONRAMP_COLLECTING_WALLET",
    "ONRAMP_AWAITING_PAYMENT",
    "ONRAMP_PROCESSING",
)


def upgrade() -> None:
    order_status = postgresql.ENUM(
        *ORDER_STATUS_VALUES, name="orderstatus", create_type=False
    )
    order_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "conversation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False, index=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False, index=True),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("token", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("currency", sa.String(length=5), nullable=False),
        sa.Column("rate", sa.Numeric(18, 6), nullable=True),
        sa.Column("output_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("paycrest_order_id", sa.String(length=100), nullable=True, unique=True, index=True),
        sa.Column("deposit_address", sa.String(length=120), nullable=True),
        sa.Column("valid_until", sa.String(length=40), nullable=True),
        sa.Column("storage_hash", sa.String(length=200), nullable=True),
        sa.Column("registry_tx_hash", sa.String(length=80), nullable=True),
        sa.Column("status", order_status, nullable=False, server_default="IDLE"),
        sa.Column("bank_name", sa.String(length=100), nullable=True),
        sa.Column("institution_code", sa.String(length=40), nullable=True),
        sa.Column("account_number", sa.String(length=20), nullable=True),
        sa.Column("account_name", sa.String(length=200), nullable=True),
        sa.Column("wallet_address", sa.String(length=42), nullable=True),
        sa.Column("network", sa.String(length=20), nullable=True),
        sa.Column("pay_bank_name", sa.String(length=120), nullable=True),
        sa.Column("pay_account_number", sa.String(length=40), nullable=True),
        sa.Column("pay_account_name", sa.String(length=200), nullable=True),
        sa.Column("pay_amount", sa.String(length=40), nullable=True),
        sa.Column("last_event", sa.String(length=60), nullable=True),
        sa.Column("last_event_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("orders")
    op.drop_table("conversation_messages")
    op.drop_table("sessions")
    postgresql.ENUM(name="orderstatus").drop(op.get_bind(), checkfirst=True)
