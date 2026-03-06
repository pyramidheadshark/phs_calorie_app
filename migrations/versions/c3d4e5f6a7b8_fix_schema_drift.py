"""fix schema drift: drop water_entries, fix recipe_entries nullability

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-06 10:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

_RECIPE_NULLABLE_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("description", sa.Text()),
    ("ingredients", postgresql.JSONB()),
    ("instructions", postgresql.JSONB()),
    ("nutrition_estimate", postgresql.JSONB()),
    ("cooking_time_min", sa.Integer()),
    ("equipment_used", postgresql.JSONB()),
    ("created_at", sa.TIMESTAMP(timezone=True)),
]


def upgrade() -> None:
    # Drop water tracking (removed from product)
    op.drop_index("idx_water_entries_user_date", table_name="water_entries")
    op.drop_table("water_entries")

    # Fix recipe_entries columns created without nullable=False
    for col, typ in _RECIPE_NULLABLE_COLS:
        op.alter_column("recipe_entries", col, existing_type=typ, nullable=False)


def downgrade() -> None:
    for col, typ in reversed(_RECIPE_NULLABLE_COLS):
        op.alter_column("recipe_entries", col, existing_type=typ, nullable=True)

    op.create_table(
        "water_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("logged_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("amount_ml", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_water_entries_user_date",
        "water_entries",
        ["user_id", "logged_at"],
    )
