"""Seed intervenciones S-4 y permisos recomendacion

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INTERVENCIONES_S4 = [
    ("control_prenatal_rutinario", "Control prenatal rutinario", "seguimiento"),
    ("seguimiento_estrecho_lc", "Seguimiento estrecho por LC corta", "seguimiento"),
    ("progesterona_vaginal", "Progesterona vaginal", "farmacologica"),
    ("tratar_infeccion", "Tratar infección activa", "farmacologica"),
    ("vigilancia_hta_multiple", "Vigilancia HTA / embarazo múltiple", "seguimiento"),
    ("derivacion_alto_riesgo", "Derivación a alto riesgo", "interconsulta"),
]

PERMISOS_RECOMENDACION = [
    (1, "recomendacion", "leer"),
    (1, "recomendacion", "ejecutar"),
    (2, "recomendacion", "leer"),
    (2, "recomendacion", "ejecutar"),
]


def upgrade() -> None:
    for codigo, nombre, categoria in INTERVENCIONES_S4:
        op.execute(
            f"""
            INSERT INTO catalogo_intervenciones (codigo, nombre, categoria)
            VALUES ('{codigo}', '{nombre}', '{categoria}')
            ON CONFLICT (codigo) DO NOTHING
            """
        )

    for rol_id, modulo, accion in PERMISOS_RECOMENDACION:
        op.execute(
            f"""
            INSERT INTO permisos (rol_id, modulo, accion)
            VALUES ({rol_id}, '{modulo}', '{accion}')
            ON CONFLICT (rol_id, modulo, accion) DO NOTHING
            """
        )


def downgrade() -> None:
    codigos = ", ".join(f"'{c}'" for c, _, _ in INTERVENCIONES_S4)
    op.execute(f"DELETE FROM catalogo_intervenciones WHERE codigo IN ({codigos})")

    for rol_id, modulo, accion in PERMISOS_RECOMENDACION:
        op.execute(
            f"""
            DELETE FROM permisos
            WHERE rol_id = {rol_id} AND modulo = '{modulo}' AND accion = '{accion}'
            """
        )
