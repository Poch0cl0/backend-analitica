"""Eliminar columna motivo de citas

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("citas", "motivo")


def downgrade() -> None:
    op.add_column("citas", sa.Column("motivo", sa.String(255), nullable=True))
