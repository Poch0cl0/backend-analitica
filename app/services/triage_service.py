"""Triage service (S-3)."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.ml_models.prediccion.predecir_s2 import AlgoritmoS2, predecir_s2
from app.ml_models.triage.predecir_s3 import predecir_urgencia
from app.models.paciente import Paciente
from app.models.triage import Triage
from app.models.usuario import Usuario
from app.schemas.triage import TriagePriorizadoResponse
from app.services.prediccion_service import PrediccionService, datos_clinicos_a_s2


def _consenso_urgencia(urgencias: list[str]) -> str:
    """Retorna el nivel más frecuente; en empate, el más grave."""
    orden = ["ROJO", "NARANJA", "AMARILLO", "VERDE"]
    conteo = {u.upper(): urgencias.count(u.upper()) for u in orden}
    max_votos = max(conteo.values())
    for nivel in orden:
        if conteo[nivel] == max_votos:
            return nivel
    return urgencias[0].upper()


def _acciones_por_nivel(nivel: str) -> list[str]:
    acciones = {
        "rojo": ["Hospitalización inmediata", "Corticoides", "Alertar equipo"],
        "naranja": ["Seguimiento estrecho", "Control en 48h", "Reevaluar LC"],
        "amarillo": ["Control prenatal intensificado", "Monitoreo semanal"],
        "verde": ["Control prenatal rutinario"],
    }
    return acciones.get(nivel.lower(), [])


class TriageService:
    @staticmethod
    def ejecutar_modelo(datos: dict) -> dict:
        return predecir_urgencia(datos)

    @staticmethod
    async def ejecutar_para_paciente(
        db: AsyncSession,
        paciente_id: int,
        prediccion_id: int,
        medico: Optional[Usuario] = None,
    ) -> dict:
        """
        Flujo completo automático usando una predicción S-2 ya guardada:
          1. Carga datos clínicos del paciente desde la BD.
          2. Carga la predicción S-2 específica (prob_prematuro ya calculada).
          3. Ejecuta S-3 (triaje / urgencia) con los datos clínicos.
          4. Guarda el triage vinculado a esa predicción.
          5. Retorna resultado completo.
        """
        from app.models.prediccion import Prediccion

        # Cargar paciente con datos clínicos
        result = await db.execute(
            select(Paciente)
            .options(selectinload(Paciente.datos_clinicos))
            .where(Paciente.id == paciente_id, Paciente.activo.is_(True))
        )
        paciente = result.scalar_one_or_none()
        if paciente is None:
            raise NotFoundError("Paciente no encontrado")

        dc = paciente.datos_clinicos
        if dc is None:
            raise BadRequestError(
                "El paciente no tiene datos clínicos registrados. "
                "Registre los datos clínicos antes de ejecutar el triaje."
            )

        # Cargar predicción específica
        pred_result = await db.execute(
            select(Prediccion).where(
                Prediccion.id == prediccion_id,
                Prediccion.paciente_id == paciente_id,
            )
        )
        prediccion = pred_result.scalar_one_or_none()
        if prediccion is None:
            raise NotFoundError(
                f"No se encontró la predicción {prediccion_id} para el paciente {paciente_id}."
            )

        campos_req = {
            "bmi": dc.bmi,
            "longitud_cervical_mm": dc.longitud_cervical_mm,
            "edad_gestacional_semanas": dc.edad_gestacional_semanas,
        }
        faltantes = [k for k, v in campos_req.items() if v is None]
        if faltantes:
            raise BadRequestError(
                f"Faltan datos clínicos obligatorios para el triaje: {faltantes}"
            )

        # Usar datos clínicos actuales del paciente como entrada a S-3
        datos_modelo = datos_clinicos_a_s2(paciente, dc)

        # S-3: clasificación de urgencia
        resultado_s3 = predecir_urgencia(datos_modelo)

        nivel_consenso = _consenso_urgencia([
            resultado_s3["urgencia_puntaje"],
            resultado_s3["urgencia_arbol"],
            resultado_s3["urgencia_ordinal"],
        ])

        # Guardar triage vinculado a la predicción elegida
        triage = await TriageService.guardar(
            db, paciente_id, resultado_s3, prediccion_id, nivel_consenso
        )

        prob = float(prediccion.prob_consenso) if prediccion.prob_consenso else None
        algoritmo = (
            prediccion.datos_entrada_snapshot.get("algoritmo_usado")
            if prediccion.datos_entrada_snapshot else None
        )

        return {
            "paciente_id":             paciente_id,
            "paciente_nombre":         f"{paciente.nombre} {paciente.apellidos}",
            "triage_id":               triage.id,
            "prediccion_id":           prediccion_id,
            "datos_entrada":           datos_modelo,
            "prob_prematuro":          prob,
            "algoritmo_s2":            algoritmo,
            "puntaje_s3":              resultado_s3["puntaje_s3"],
            "urgencia_puntaje":        resultado_s3["urgencia_puntaje"],
            "urgencia_arbol":          resultado_s3["urgencia_arbol"],
            "urgencia_ordinal":        resultado_s3["urgencia_ordinal"],
            "nivel_urgencia_consenso": nivel_consenso,
        }

    @staticmethod
    async def guardar(
        db: AsyncSession,
        paciente_id: int,
        resultado: dict,
        prediccion_id: Optional[int] = None,
        nivel_consenso: Optional[str] = None,
    ) -> Triage:
        nivel = (nivel_consenso or resultado["urgencia_puntaje"]).lower()
        triage = Triage(
            paciente_id=paciente_id,
            prediccion_id=prediccion_id,
            nivel_urgencia=nivel,
            score_formula_ponderada=Decimal(str(resultado["puntaje_s3"])),
            urgencia_arbol=resultado["urgencia_arbol"].lower(),
            urgencia_ordinal=resultado["urgencia_ordinal"].lower(),
            factores_activos_detalle=resultado.get("features_s3"),
        )
        db.add(triage)
        await db.flush()
        await db.refresh(triage)
        return triage

    @staticmethod
    async def resumen(db: AsyncSession, medico_id: int | None = None) -> dict:
        medico_filter = "AND p.medico_asignado_id = :medico_id" if medico_id else ""
        result = await db.execute(text(f"""
            SELECT LOWER(t.nivel_urgencia) AS nivel, COUNT(*) AS total
            FROM triage t
            JOIN pacientes p ON p.id = t.paciente_id
            WHERE t.id IN (
                SELECT DISTINCT ON (paciente_id) id FROM triage
                ORDER BY paciente_id, fecha_triage DESC
            )
            {medico_filter}
            GROUP BY LOWER(t.nivel_urgencia)
        """), {"medico_id": medico_id} if medico_id else {})
        counts = {row["nivel"]: row["total"] for row in result.mappings().all()}
        return {
            "rojo": counts.get("rojo", 0),
            "naranja": counts.get("naranja", 0),
            "amarillo": counts.get("amarillo", 0),
            "verde": counts.get("verde", 0),
        }

    @staticmethod
    async def listar_priorizados(
        db: AsyncSession,
        nivel: str | None = None,
        algoritmo: str = "consenso",
        medico_id: int | None = None,
    ) -> list[TriagePriorizadoResponse]:
        col_map = {
            "arbol": "LOWER(v.urgencia_arbol)",
            "ordinal": "LOWER(v.urgencia_ordinal)",
            "consenso": "LOWER(v.nivel_urgencia)",
        }
        col = col_map.get(algoritmo, "LOWER(v.nivel_urgencia)")

        sql = """
            SELECT v.* FROM vista_triage_priorizado v
            JOIN pacientes p ON p.id = v.paciente_id
        """
        params: dict = {}
        conditions: list[str] = []
        if medico_id:
            conditions.append("""
                (
                  p.medico_asignado_id = :medico_id
                  OR EXISTS (
                    SELECT 1 FROM citas c
                    WHERE c.paciente_id = p.id AND c.medico_id = :medico_id
                  )
                )
            """)
            params["medico_id"] = medico_id
        if nivel:
            conditions.append("LOWER(v.nivel_urgencia) = :nivel")
            params["nivel"] = nivel.lower()
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
        out = []
        for row in rows:
            data = dict(row)
            # Nivel efectivo según algoritmo seleccionado
            if algoritmo == "arbol":
                nivel_efectivo = data.get("urgencia_arbol") or data.get("nivel_urgencia")
            elif algoritmo == "ordinal":
                nivel_efectivo = data.get("urgencia_ordinal") or data.get("nivel_urgencia")
            else:
                nivel_efectivo = data.get("nivel_urgencia")
            data["nivel_urgencia"] = nivel_efectivo
            data["acciones_urgentes"] = _acciones_por_nivel(nivel_efectivo or "")
            out.append(TriagePriorizadoResponse(**data))
        return out

    @staticmethod
    async def recalcular(
        db: AsyncSession,
        paciente_id: int,
        datos: dict,
        medico: Optional[Usuario] = None,
    ) -> Triage:
        """Recalcula triaje con datos ingresados manualmente."""
        resultado_s3 = TriageService.ejecutar_modelo(datos)
        resultado_s2 = PrediccionService.ejecutar_modelo(datos)
        prediccion = await PrediccionService.guardar(
            db, paciente_id, datos, resultado_s2, medico
        )
        nivel_consenso = _consenso_urgencia([
            resultado_s3["urgencia_puntaje"],
            resultado_s3["urgencia_arbol"],
            resultado_s3["urgencia_ordinal"],
        ])
        return await TriageService.guardar(
            db, paciente_id, resultado_s3, prediccion.id, nivel_consenso
        )

    @staticmethod
    async def procesar_pendientes(
        db: AsyncSession,
        medico_id: int | None = None,
        forzar: bool = False,
        medico: Optional[Usuario] = None,
    ) -> int:
        """
        Genera triaje para pacientes elegibles:
        - Con predicción pero sin triaje (modo normal).
        - Con datos clínicos completos: ejecuta predicción + triaje si falta predicción.
        - Con forzar=True: re-triage de todos los pacientes elegibles del médico (o todos si admin).
        """
        medico_filter = ""
        if medico_id:
            medico_filter = """
              AND (
                p.medico_asignado_id = :medico_id
                OR EXISTS (
                  SELECT 1 FROM citas c
                  WHERE c.paciente_id = p.id AND c.medico_id = :medico_id
                )
              )
            """

        pending_filter = ""
        if not forzar:
            pending_filter = """
              AND NOT EXISTS (SELECT 1 FROM triage t WHERE t.paciente_id = p.id)
            """

        sql = f"""
            SELECT p.id AS paciente_id,
              (
                SELECT pr.id FROM predicciones pr
                WHERE pr.paciente_id = p.id
                ORDER BY pr.fecha_prediccion DESC
                LIMIT 1
              ) AS prediccion_id
            FROM pacientes p
            INNER JOIN datos_clinicos dc ON dc.paciente_id = p.id
            WHERE p.activo = true
              AND dc.bmi IS NOT NULL
              AND dc.longitud_cervical_mm IS NOT NULL
              AND dc.edad_gestacional_semanas IS NOT NULL
              {pending_filter}
              {medico_filter}
        """
        params: dict = {}
        if medico_id:
            params["medico_id"] = medico_id

        result = await db.execute(text(sql), params)
        rows = result.mappings().all()

        procesados = 0
        for row in rows:
            paciente_id = row["paciente_id"]
            prediccion_id = row["prediccion_id"]
            try:
                if prediccion_id is None:
                    await PrediccionService.ejecutar_consenso_para_paciente(
                        db, paciente_id, medico=medico
                    )
                else:
                    await TriageService.ejecutar_para_paciente(
                        db, paciente_id, prediccion_id, medico=medico
                    )
                procesados += 1
            except Exception:
                continue
        return procesados

    @staticmethod
    async def procesar_pendientes_medico(
        db: AsyncSession,
        medico_id: int,
        medico: Optional[Usuario] = None,
        forzar: bool = False,
    ) -> int:
        return await TriageService.procesar_pendientes(
            db, medico_id=medico_id, forzar=forzar, medico=medico
        )
