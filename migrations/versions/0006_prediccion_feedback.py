"""Crear tabla prediccion_feedback

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISOS_FEEDBACK = [
    (1, "prediccion", "feedback"),
    (2, "prediccion", "feedback"),
]


def upgrade() -> None:
    op.create_table(
        "prediccion_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("prediccion_id", sa.Integer(), sa.ForeignKey("predicciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("medico_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("modelo", sa.String(50), nullable=True),
        sa.Column("voto_correcta", sa.Boolean(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prediccion_feedback_prediccion", "prediccion_feedback", ["prediccion_id"])
    op.create_index("ix_prediccion_feedback_medico", "prediccion_feedback", ["medico_id"])

    for rol_id, modulo, accion in PERMISOS_FEEDBACK:
        op.execute(
            f"""
            INSERT INTO permisos (rol_id, modulo, accion)
            VALUES ({rol_id}, '{modulo}', '{accion}')
            ON CONFLICT (rol_id, modulo, accion) DO NOTHING
            """
        )


def downgrade() -> None:
    for rol_id, modulo, accion in PERMISOS_FEEDBACK:
        op.execute(
            f"""
            DELETE FROM permisos
            WHERE rol_id = {rol_id} AND modulo = '{modulo}' AND accion = '{accion}'
            """
        )

    op.drop_table("prediccion_feedback")
