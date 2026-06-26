"""Actualizar datos_clinicos: embarazo_multiple BOOLEAN -> INTEGER

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Views/funciones que dependen de datos_clinicos.embarazo_multiple
_DEPENDENCIAS = [
    "DROP VIEW IF EXISTS vista_triage_priorizado CASCADE",
    "DROP VIEW IF EXISTS vista_perfil_completo CASCADE",
    "DROP FUNCTION IF EXISTS obtener_snapshot_clinico(INT)",
]

_VISTA_TRIAGE = """
CREATE OR REPLACE VIEW vista_triage_priorizado AS
SELECT
    p.id AS paciente_id,
    p.nombre,
    p.apellidos,
    p.dni,
    dc.edad_gestacional_semanas,
    dc.embarazo_multiple,
    dc.parto_prematuro_previo,
    dc.longitud_cervical_mm,
    dc.hipertension_gestacional,
    dc.infeccion_activa,
    dc.bmi,
    dc.bmi_categoria,
    dc.num_condiciones_cronicas,
    t.nivel_urgencia,
    t.score_formula_ponderada,
    t.factores_activos_detalle,
    t.acciones_urgentes,
    pred.prob_consenso,
    pred.semanas_estimadas_consenso,
    t.fecha_triage
FROM triage t
JOIN pacientes p ON t.paciente_id = p.id
JOIN datos_clinicos dc ON dc.paciente_id = p.id
JOIN predicciones pred ON t.prediccion_id = pred.id
WHERE t.id IN (
    SELECT DISTINCT ON (paciente_id) id
    FROM triage ORDER BY paciente_id, fecha_triage DESC
)
ORDER BY
    CASE t.nivel_urgencia
        WHEN 'rojo' THEN 1
        WHEN 'naranja' THEN 2
        WHEN 'amarillo' THEN 3
        WHEN 'verde' THEN 4
    END,
    t.score_formula_ponderada DESC;
"""

_VISTA_PERFIL = """
CREATE OR REPLACE VIEW vista_perfil_completo AS
SELECT
    p.id,
    p.dni,
    p.nombre,
    p.apellidos,
    p.telefono_principal,
    p.email,
    EXTRACT(YEAR FROM age(CURRENT_DATE, p.fecha_nacimiento))::INT AS edad_madre,
    dc.edad_gestacional_semanas,
    dc.longitud_cervical_mm,
    dc.embarazo_multiple,
    dc.parto_prematuro_previo,
    dc.hipertension_gestacional,
    dc.bmi,
    dc.bmi_categoria,
    dc.num_condiciones_cronicas,
    dc.infeccion_activa,
    dc.alerta_activa,
    dc.notas_medicas,
    pred.prob_consenso,
    pred.nivel_riesgo,
    pred.semanas_estimadas_consenso,
    pred.fecha_prediccion AS fecha_ultima_prediccion,
    tri.nivel_urgencia,
    tri.factores_activos_detalle,
    tri.acciones_urgentes,
    tri.fecha_triage AS fecha_ultimo_triage,
    u.nombre AS medico_nombre,
    u.apellidos AS medico_apellidos
FROM pacientes p
JOIN datos_clinicos dc ON dc.paciente_id = p.id
LEFT JOIN usuarios u ON u.id = p.medico_asignado_id
LEFT JOIN LATERAL (
    SELECT prob_consenso, nivel_riesgo, semanas_estimadas_consenso, fecha_prediccion
    FROM predicciones WHERE paciente_id = p.id
    ORDER BY fecha_prediccion DESC LIMIT 1
) pred ON true
LEFT JOIN LATERAL (
    SELECT nivel_urgencia, factores_activos_detalle, acciones_urgentes, fecha_triage
    FROM triage WHERE paciente_id = p.id
    ORDER BY fecha_triage DESC LIMIT 1
) tri ON true
WHERE p.activo = true;
"""

_FUNC_SNAPSHOT = """
CREATE OR REPLACE FUNCTION obtener_snapshot_clinico(p_paciente_id INT)
RETURNS JSONB AS $$
DECLARE
    v_snapshot JSONB;
BEGIN
    SELECT jsonb_build_object(
        'edad_madre', EXTRACT(YEAR FROM age(CURRENT_DATE, pac.fecha_nacimiento)),
        'semanas_gestacion', dc.edad_gestacional_semanas,
        'longitud_cervical_mm', dc.longitud_cervical_mm,
        'embarazo_multiple', dc.embarazo_multiple,
        'parto_prematuro_previo', dc.parto_prematuro_previo,
        'hipertension_gestacional', dc.hipertension_gestacional,
        'bmi', dc.bmi,
        'bmi_categoria', dc.bmi_categoria,
        'num_condiciones_cronicas', dc.num_condiciones_cronicas,
        'infeccion_activa', dc.infeccion_activa,
        'diabetes_pregestacional', dc.diabetes_pregestacional,
        'diabetes_gestacional', dc.diabetes_gestacional,
        'hipertension_cronica', dc.hipertension_cronica,
        'eclampsia', dc.eclampsia,
        'hepatitis_b', dc.hepatitis_b,
        'hepatitis_c', dc.hepatitis_c,
        'sifilis', dc.sifilis,
        'clamidia', dc.clamidia,
        'gonorrea', dc.gonorrea,
        'cesareas_previas', dc.cesareas_previas,
        'num_cesareas', dc.num_cesareas,
        'num_partos_previos_vivos', dc.num_partos_previos_vivos
    ) INTO v_snapshot
    FROM pacientes pac
    JOIN datos_clinicos dc ON dc.paciente_id = pac.id
    WHERE pac.id = p_paciente_id AND pac.activo = true;

    RETURN v_snapshot;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    # 1. Eliminar dependencias
    for sql in _DEPENDENCIAS:
        op.execute(sql)

    # 2. Eliminar default actual (boolean)
    op.alter_column("datos_clinicos", "embarazo_multiple", server_default=None)

    # 3. Cambiar tipo BOOLEAN -> SMALLINT
    op.alter_column(
        "datos_clinicos",
        "embarazo_multiple",
        type_=sa.SmallInteger(),
        existing_type=sa.Boolean(),
        postgresql_using="CASE WHEN embarazo_multiple IS TRUE THEN 2 ELSE 1 END",
    )

    # 4. Nuevo default
    op.alter_column(
        "datos_clinicos",
        "embarazo_multiple",
        server_default=sa.text("1"),
    )

    # 5. Recrear vistas y función
    op.execute(_VISTA_TRIAGE)
    op.execute(_VISTA_PERFIL)
    op.execute(_FUNC_SNAPSHOT)


def downgrade() -> None:
    # 1. Eliminar dependencias
    for sql in _DEPENDENCIAS:
        op.execute(sql)

    # 2. Eliminar default actual (integer)
    op.alter_column("datos_clinicos", "embarazo_multiple", server_default=None)

    # 3. Cambiar tipo SMALLINT -> BOOLEAN
    op.alter_column(
        "datos_clinicos",
        "embarazo_multiple",
        type_=sa.Boolean(),
        existing_type=sa.SmallInteger(),
        postgresql_using="CASE WHEN embarazo_multiple > 1 THEN true ELSE false END",
    )

    # 4. Restaurar default anterior
    op.alter_column(
        "datos_clinicos",
        "embarazo_multiple",
        server_default=sa.text("false"),
    )

    # 5. Recrear vistas y función (con tipos originales)
    op.execute(_VISTA_TRIAGE)
    op.execute(_VISTA_PERFIL)
    op.execute(_FUNC_SNAPSHOT)
