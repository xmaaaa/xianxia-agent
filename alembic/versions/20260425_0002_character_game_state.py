"""add character game state

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-25

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("location", sa.String(length=128), server_default="青云镇", nullable=False),
    )
    op.add_column(
        "characters",
        sa.Column("inventory", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.add_column(
        "characters",
        sa.Column("event_log", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.alter_column("characters", "location", server_default=None)
    op.alter_column("characters", "inventory", server_default=None)
    op.alter_column("characters", "event_log", server_default=None)


def downgrade() -> None:
    op.drop_column("characters", "event_log")
    op.drop_column("characters", "inventory")
    op.drop_column("characters", "location")
