"""initial characters table

Revision ID: 0001
Revises:
Create Date: 2026-04-02

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sect", sa.String(length=128), nullable=False),
        sa.Column("spirit_root", sa.String(length=256), nullable=False),
        sa.Column("realm", sa.String(length=64), server_default="炼气初期", nullable=False),
        sa.Column("exp", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_characters_user_id", "characters", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_characters_user_id", table_name="characters")
    op.drop_table("characters")
