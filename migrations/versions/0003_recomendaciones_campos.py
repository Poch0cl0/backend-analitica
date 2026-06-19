"""Ampliar recomendaciones para gestión UI

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recomendaciones", sa.Column("titulo", sa.String(200)))
    op.add_column("recomendaciones", sa.Column("descripcion", sa.Text()))
    op.add_column("recomendaciones", sa.Column("notas", sa.Text()))
    op.add_column("recomendaciones", sa.Column("fecha_revision", sa.Date()))
    op.add_column(
        "recomendaciones",
        sa.Column("medico_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
    )
    op.add_column(
        "recomendaciones",
        sa.Column("es_manual", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "recomendaciones",
        sa.Column("origen", sa.String(20), server_default=sa.text("'s4_auto'"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("recomendaciones", "origen")
    op.drop_column("recomendaciones", "es_manual")
    op.drop_column("recomendaciones", "medico_id")
    op.drop_column("recomendaciones", "fecha_revision")
    op.drop_column("recomendaciones", "notas")
    op.drop_column("recomendaciones", "descripcion")
    op.drop_column("recomendaciones", "titulo")
