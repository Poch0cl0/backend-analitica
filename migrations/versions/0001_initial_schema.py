"""Initial schema with corrections

Revision ID: 0001
Revises:
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  # --- roles ---
  op.create_table(
      "roles",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("nombre", sa.String(50), nullable=False, unique=True),
      sa.Column("descripcion", sa.Text()),
  )

  # --- permisos ---
  op.create_table(
      "permisos",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
      sa.Column("modulo", sa.String(50), nullable=False),
      sa.Column("accion", sa.String(50), nullable=False),
      sa.UniqueConstraint("rol_id", "modulo", "accion", name="uq_permiso_rol_modulo_accion"),
  )

  # --- usuarios ---
  op.create_table(
      "usuarios",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("email", sa.String(255), nullable=False, unique=True),
      sa.Column("password_hash", sa.String(255), nullable=False),
      sa.Column("nombre", sa.String(100), nullable=False),
      sa.Column("apellidos", sa.String(100), nullable=False),
      sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
      sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- pacientes ---
  op.create_table(
      "pacientes",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("dni", sa.String(20), nullable=False, unique=True),
      sa.Column("nombre", sa.String(100), nullable=False),
      sa.Column("apellidos", sa.String(100), nullable=False),
      sa.Column("fecha_nacimiento", sa.Date(), nullable=False),
      sa.Column("telefono_principal", sa.String(20)),
      sa.Column("email", sa.String(255)),
      sa.Column("medico_asignado_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
      sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- datos_clinicos ---
  op.create_table(
      "datos_clinicos",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, unique=True),
      sa.Column("edad_gestacional_semanas", sa.Integer()),
      sa.Column("longitud_cervical_mm", sa.Numeric(5, 2)),
      sa.Column("embarazo_multiple", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("parto_prematuro_previo", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("hipertension_gestacional", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("bmi", sa.Numeric(5, 2)),
      sa.Column("bmi_categoria", sa.String(30)),
      sa.Column("num_condiciones_cronicas", sa.Integer(), server_default=sa.text("0")),
      sa.Column("infeccion_activa", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("diabetes_pregestacional", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("diabetes_gestacional", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("hipertension_cronica", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("eclampsia", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("hepatitis_b", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("hepatitis_c", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("sifilis", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("clamidia", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("gonorrea", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("cesareas_previas", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("num_cesareas", sa.Integer(), server_default=sa.text("0")),
      sa.Column("num_partos_previos_vivos", sa.Integer(), server_default=sa.text("0")),
      sa.Column("alerta_activa", sa.Boolean(), server_default=sa.text("false")),
      sa.Column("notas_medicas", sa.Text()),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- citas ---
  op.create_table(
      "citas",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
      sa.Column("medico_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
      sa.Column("fecha_hora", sa.DateTime(), nullable=False),
      sa.Column("duracion_minutos", sa.Integer(), server_default=sa.text("30")),
      sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'programada'")),
      sa.Column("motivo", sa.String(255)),
      sa.Column("notas", sa.Text()),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- catalogo_intervenciones ---
  op.create_table(
      "catalogo_intervenciones",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("codigo", sa.String(50), nullable=False, unique=True),
      sa.Column("nombre", sa.String(200), nullable=False),
      sa.Column("descripcion", sa.Text()),
      sa.Column("categoria", sa.String(50)),
      sa.Column("activo", sa.Boolean(), server_default=sa.text("true")),
  )

  # --- predicciones (con prob_logistica, no prob_svm) ---
  op.create_table(
      "predicciones",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
      sa.Column("datos_entrada_snapshot", postgresql.JSONB(), nullable=False),
      sa.Column("fecha_prediccion", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("prob_random_forest", sa.Numeric(5, 4)),
      sa.Column("semanas_estimadas_rf", sa.Integer()),
      sa.Column("prob_catboost", sa.Numeric(5, 4)),
      sa.Column("semanas_estimadas_cb", sa.Integer()),
      sa.Column("prob_logistica", sa.Numeric(5, 4)),
      sa.Column("semanas_estimadas_logistica", sa.Integer()),
      sa.Column("prob_consenso", sa.Numeric(5, 4)),
      sa.Column("semanas_estimadas_consenso", sa.Integer()),
      sa.Column("nivel_riesgo", sa.String(10)),
      sa.Column("shap_values", postgresql.JSONB()),
      sa.Column("medico_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.CheckConstraint(
          "nivel_riesgo IN ('critico','alto','medio','bajo')",
          name="ck_predicciones_nivel_riesgo",
      ),
  )

  # --- triage ---
  op.create_table(
      "triage",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
      sa.Column("prediccion_id", sa.Integer(), sa.ForeignKey("predicciones.id", ondelete="SET NULL")),
      sa.Column("nivel_urgencia", sa.String(10), nullable=False),
      sa.Column("score_formula_ponderada", sa.Numeric(5, 4)),
      sa.Column("urgencia_arbol", sa.String(10)),
      sa.Column("urgencia_ordinal", sa.String(10)),
      sa.Column("factores_activos_detalle", postgresql.JSONB()),
      sa.Column("acciones_urgentes", postgresql.JSONB()),
      sa.Column("fecha_triage", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- recomendaciones ---
  op.create_table(
      "recomendaciones",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
      sa.Column("prediccion_id", sa.Integer(), sa.ForeignKey("predicciones.id", ondelete="SET NULL")),
      sa.Column("intervencion_id", sa.Integer(), sa.ForeignKey("catalogo_intervenciones.id", ondelete="RESTRICT"), nullable=False),
      sa.Column("algoritmo", sa.String(30), nullable=False),
      sa.Column("prioridad", sa.Integer()),
      sa.Column("confianza", sa.Numeric(5, 4)),
      sa.Column("estado", sa.String(20), server_default=sa.text("'pendiente'")),
      sa.Column("fecha_recomendacion", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- parametros_sistema ---
  op.create_table(
      "parametros_sistema",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("clave", sa.String(100), nullable=False, unique=True),
      sa.Column("valor", sa.Text(), nullable=False),
      sa.Column("descripcion", sa.Text()),
      sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- auditoria ---
  op.create_table(
      "auditoria",
      sa.Column("id", sa.Integer(), primary_key=True),
      sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
      sa.Column("accion", sa.String(100), nullable=False),
      sa.Column("modulo", sa.String(50), nullable=False),
      sa.Column("entidad_id", sa.Integer()),
      sa.Column("detalle", postgresql.JSONB()),
      sa.Column("ip_address", sa.String(45)),
      sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
  )

  # --- Seed roles ---
  op.execute("""
      INSERT INTO roles (id, nombre, descripcion) VALUES
      (1, 'admin', 'Administrador del sistema'),
      (2, 'medico', 'Médico obstetra'),
      (3, 'secretaria', 'Secretaria / recepción')
  """)

  # --- Seed permisos ---
  op.execute("""
      INSERT INTO permisos (rol_id, modulo, accion) VALUES
      -- admin: todo
      (1, 'usuarios', 'leer'), (1, 'usuarios', 'crear'), (1, 'usuarios', 'actualizar'), (1, 'usuarios', 'eliminar'),
      (1, 'pacientes', 'leer'), (1, 'pacientes', 'crear'), (1, 'pacientes', 'actualizar'), (1, 'pacientes', 'eliminar'),
      (1, 'citas', 'leer'), (1, 'citas', 'crear'), (1, 'citas', 'actualizar'), (1, 'citas', 'eliminar'),
      (1, 'datos_clinicos', 'leer'), (1, 'datos_clinicos', 'crear'), (1, 'datos_clinicos', 'actualizar'),
      (1, 'prediccion', 'ejecutar'), (1, 'triage', 'leer'), (1, 'triage', 'ejecutar'),
      (1, 'reportes', 'exportar'),
      -- medico
      (2, 'pacientes', 'leer'),
      (2, 'citas', 'leer'), (2, 'citas', 'actualizar'),
      (2, 'datos_clinicos', 'leer'), (2, 'datos_clinicos', 'crear'), (2, 'datos_clinicos', 'actualizar'),
      (2, 'prediccion', 'ejecutar'), (2, 'triage', 'leer'), (2, 'triage', 'ejecutar'),
      (2, 'reportes', 'exportar'),
      -- secretaria
      (3, 'pacientes', 'leer'), (3, 'pacientes', 'crear'), (3, 'pacientes', 'actualizar'), (3, 'pacientes', 'eliminar'),
      (3, 'citas', 'leer'), (3, 'citas', 'crear'), (3, 'citas', 'actualizar'), (3, 'citas', 'eliminar');
  """)

  # --- Vista permisos por rol ---
  op.execute("""
      CREATE OR REPLACE VIEW vista_permisos_rol AS
      SELECT r.nombre AS rol, p.modulo, p.accion
      FROM permisos p
      JOIN roles r ON r.id = p.rol_id;
  """)

  # --- Vista triage priorizado (con bmi y num_condiciones) ---
  op.execute("""
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
  """)

  # --- Vista perfil completo ---
  op.execute("""
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
  """)

  # --- Función snapshot clínico ---
  op.execute("""
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
  """)

  # --- Comentarios científicos (uno por op.execute — asyncpg no acepta múltiples sentencias) ---
  op.execute("COMMENT ON COLUMN datos_clinicos.bmi IS 'Índice de Masa Corporal. Obesidad grave (>40) clasificada como factor de riesgo altamente sugerente (Mitrogiannis et al., 2023)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.longitud_cervical_mm IS 'Longitud cervical. ≤25 mm asociado con riesgo 3.2x mayor de parto prematuro espontáneo (p=0.008, Kyparissidis-Kokkinidis et al., 2024)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.parto_prematuro_previo IS 'Antecedente de parto prematuro. Presente en el 40% del grupo de alto riesgo (p=0.01). Predictor en nomograma (Borboa-Olivares et al., 2023; Lee et al., 2020)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.embarazo_multiple IS 'Nodo más importante en árbol CART (86.4% asociado a parto prematuro). Factor de riesgo incluido en modelos (Gulati et al., 2024; Lee et al., 2020)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.hipertension_gestacional IS 'Presión diastólica en tercer trimestre con alto SHAP. Factor de riesgo identificado (Yu et al., 2024; Gulati et al., 2024)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.edad_gestacional_semanas IS 'Edad gestacional en semanas. Usada para estratificar modelos por trimestre (AUC 0.70). Predictor clave en parto temprano (Yu et al., 2024; Lee et al., 2020)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.num_condiciones_cronicas IS 'Número de condiciones crónicas activas. Enfermedades como hepatitis C aumentan riesgo (OR 1.99). Requiere seguimiento especializado (Gulersen et al., 2024)'")
  op.execute("COMMENT ON COLUMN datos_clinicos.infeccion_activa IS 'Infección activa (ITS). Citoquinas inflamatorias elevadas en alto riesgo (Borboa-Olivares et al., 2023; Gulati et al., 2024)'")


def downgrade() -> None:
  op.execute("DROP FUNCTION IF EXISTS obtener_snapshot_clinico(INT)")
  op.execute("DROP VIEW IF EXISTS vista_perfil_completo")
  op.execute("DROP VIEW IF EXISTS vista_triage_priorizado")
  op.execute("DROP VIEW IF EXISTS vista_permisos_rol")
  op.drop_table("auditoria")
  op.drop_table("parametros_sistema")
  op.drop_table("recomendaciones")
  op.drop_table("triage")
  op.drop_table("predicciones")
  op.drop_table("catalogo_intervenciones")
  op.drop_table("citas")
  op.drop_table("datos_clinicos")
  op.drop_table("pacientes")
  op.drop_table("usuarios")
  op.drop_table("permisos")
  op.drop_table("roles")
