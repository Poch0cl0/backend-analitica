"""Historial de contactos con pacientes

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contactos_paciente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "paciente_id",
            sa.Integer(),
            sa.ForeignKey("pacientes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("nota", sa.Text(), nullable=False),
        sa.Column(
            "medico_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("contactos_paciente")
