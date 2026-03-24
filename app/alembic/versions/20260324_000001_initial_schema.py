"""initial schema

Revision ID: 20260324_000001
Revises:
Create Date: 2026-03-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260324_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


profile_kind = sa.Enum("USER", "ADMIN", name="roleenum")
quote_side = sa.Enum("ASK", "BID", name="directionenum")
ticket_state = sa.Enum("NEW", "EXECUTED", "PARTIALLY_EXECUTED", "CANCELLED", name="orderstatusenum")


def upgrade() -> None:
    profile_kind.create(op.get_bind(), checkfirst=True)
    quote_side.create(op.get_bind(), checkfirst=True)
    ticket_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "instruments",
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("ticker"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", profile_kind, nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column("api_key", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_ticker", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("filled", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("direction", quote_side, nullable=False),
        sa.Column("status", ticket_state, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_ticker"], ["instruments.ticker"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_from_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("instrument_ticker", sa.String(length=10), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_ticker"], ["instruments.ticker"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_from_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_inventories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_ticker", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_ticker"], ["instruments.ticker"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_inventories")
    op.drop_table("transactions")
    op.drop_table("orders")
    op.drop_table("users")
    op.drop_table("instruments")

    ticket_state.drop(op.get_bind(), checkfirst=True)
    quote_side.drop(op.get_bind(), checkfirst=True)
    profile_kind.drop(op.get_bind(), checkfirst=True)
