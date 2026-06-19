"""Predicción service."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.ml_models.prediccion.predecir_s2 import AlgoritmoS2, predecir_s2, predecir_s2_consenso
from app.models.datos_clinicos import DatosClinicos
from app.models.paciente import Paciente
from app.models.prediccion import Prediccion
from app.models.triage import Triage
from app.models.usuario import Usuario


def _edad_en_anios(fecha_nac: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nac.year - (
        (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)
    )


def datos_clinicos_a_s2(paciente: Paciente, dc: DatosClinicos) -> dict:
    """Mapea los datos clínicos del paciente a los campos que espera el modelo S-2."""
    return {
        "mager":                    float(_edad_en_anios(paciente.fecha_nacimiento)),
        "rf_ppterm":                "Y" if dc.parto_prematuro_previo else "N",
        "dplural":                  2 if dc.embarazo_multiple else 1,
        "num_condiciones_cronicas": int(dc.num_condiciones_cronicas),
        "infeccion_activa":         1 if dc.infeccion_activa else 0,
        "priorlive":                int(dc.num_partos_previos_vivos),
        "bmi":                      float(dc.bmi) if dc.bmi else 22.0,
        "cl_sim_mm":                float(dc.longitud_cervical_mm) if dc.longitud_cervical_mm else 30.0,
        "combgest":                 float(dc.edad_gestacional_semanas) if dc.edad_gestacional_semanas else 36.0,
        # campo extra para S-3
        "rf_ghype":                 "Y" if dc.hipertension_gestacional else "N",
    }


class PrediccionService:
    @staticmethod
    def ejecutar_modelo(datos: dict, algoritmo: AlgoritmoS2 = "mejor") -> dict:
        return predecir_s2(datos, algoritmo=algoritmo)

    @staticmethod
    def ejecutar_consenso(datos: dict) -> dict:
        return predecir_s2_consenso(datos)

    @staticmethod
    async def _obtener_paciente_con_datos(db: AsyncSession, paciente_id: int) -> tuple[Paciente, DatosClinicos]:
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
                "Registre los datos clínicos antes de ejecutar la predicción."
            )

        campos_requeridos = {
            "bmi": dc.bmi,
            "longitud_cervical_mm": dc.longitud_cervical_mm,
            "edad_gestacional_semanas": dc.edad_gestacional_semanas,
        }
        faltantes = [k for k, v in campos_requeridos.items() if v is None]
        if faltantes:
            raise BadRequestError(
                f"Faltan datos clínicos obligatorios para la predicción: {faltantes}"
            )
        return paciente, dc

    @staticmethod
    async def ejecutar_consenso_para_paciente(
        db: AsyncSession,
        paciente_id: int,
        medico: Optional[Usuario] = None,
    ) -> dict:
        paciente, dc = await PrediccionService._obtener_paciente_con_datos(db, paciente_id)
        datos_modelo = datos_clinicos_a_s2(paciente, dc)
        resultado = predecir_s2_consenso(datos_modelo)
        prediccion = await PrediccionService.guardar_consenso(
            db, paciente_id, datos_modelo, resultado, medico
        )
        await PrediccionService._generar_triage_automatico(
            db, paciente_id, prediccion.id, medico
        )
        return {
            "prediccion_id": prediccion.id,
            "prob_consenso": resultado["prob_consenso"],
            "nivel_riesgo": resultado["nivel_riesgo"],
            "modelos": resultado["modelos"],
        }

    @staticmethod
    async def _generar_triage_automatico(
        db: AsyncSession,
        paciente_id: int,
        prediccion_id: int,
        medico: Optional[Usuario] = None,
    ) -> None:
        """Tras guardar una predicción, registra triaje automáticamente si aún no existe."""
        from app.services.triage_service import TriageService

        existe = await db.execute(
            select(Triage.id).where(Triage.paciente_id == paciente_id).limit(1)
        )
        if existe.scalar_one_or_none() is not None:
            return
        try:
            await TriageService.ejecutar_para_paciente(
                db, paciente_id, prediccion_id, medico=medico
            )
        except Exception:
            pass

    @staticmethod
    async def obtener_ultima_consenso(db: AsyncSession, paciente_id: int) -> dict | None:
        result = await db.execute(
            select(Prediccion)
            .where(Prediccion.paciente_id == paciente_id)
            .order_by(Prediccion.fecha_prediccion.desc())
            .limit(1)
        )
        pred = result.scalar_one_or_none()
        if pred is None or pred.prob_consenso is None:
            return None

        def _item(prob, sem) -> dict | None:
            if prob is None:
                return None
            return {
                "prob_prematuro": float(prob),
                "semanas_estimadas": float(sem) if sem is not None else 0.0,
            }

        rf = _item(pred.prob_random_forest, pred.semanas_estimadas_rf)
        cb = _item(pred.prob_catboost, pred.semanas_estimadas_cb)
        svm = _item(pred.prob_logistica, pred.semanas_estimadas_logistica)
        if not all([rf, cb, svm]):
            return None

        return {
            "prediccion_id": pred.id,
            "prob_consenso": float(pred.prob_consenso),
            "nivel_riesgo": pred.nivel_riesgo,
            "modelos": {
                "random_forest": rf,
                "catboost": cb,
                "svm": svm,
            },
            "fecha_prediccion": pred.fecha_prediccion,
        }

    @staticmethod
    async def guardar(
        db: AsyncSession,
        paciente_id: int,
        datos_entrada: dict,
        resultado: dict,
        medico: Optional[Usuario] = None,
    ) -> Prediccion:
        prob = resultado["prob_prematuro"]
        nivel = "bajo"
        if prob >= 0.7:
            nivel = "critico"
        elif prob >= 0.5:
            nivel = "alto"
        elif prob >= 0.3:
            nivel = "medio"

        prediccion = Prediccion(
            paciente_id=paciente_id,
            datos_entrada_snapshot={
                **datos_entrada,
                "algoritmo_usado": resultado.get("algoritmo_usado"),
                "archivo_modelo":  resultado.get("archivo_modelo"),
            },
            prob_logistica=Decimal(str(prob)),
            semanas_estimadas_logistica=int(round(resultado["semanas_estimadas"])),
            prob_consenso=Decimal(str(prob)),
            semanas_estimadas_consenso=int(round(resultado["semanas_estimadas"])),
            nivel_riesgo=nivel,
            medico_id=medico.id if medico else None,
        )
        db.add(prediccion)
        await db.flush()
        await db.refresh(prediccion)
        return prediccion

    @staticmethod
    async def guardar_consenso(
        db: AsyncSession,
        paciente_id: int,
        datos_entrada: dict,
        resultado: dict,
        medico: Optional[Usuario] = None,
    ) -> Prediccion:
        m = resultado["modelos"]
        prediccion = Prediccion(
            paciente_id=paciente_id,
            datos_entrada_snapshot={**datos_entrada, "modo": "consenso"},
            prob_random_forest=Decimal(str(m["random_forest"]["prob_prematuro"])),
            semanas_estimadas_rf=int(round(m["random_forest"]["semanas_estimadas"])),
            prob_catboost=Decimal(str(m["catboost"]["prob_prematuro"])),
            semanas_estimadas_cb=int(round(m["catboost"]["semanas_estimadas"])),
            prob_logistica=Decimal(str(m["svm"]["prob_prematuro"])),
            semanas_estimadas_logistica=int(round(m["svm"]["semanas_estimadas"])),
            prob_consenso=Decimal(str(resultado["prob_consenso"])),
            semanas_estimadas_consenso=int(round(resultado["semanas_estimadas_consenso"])),
            nivel_riesgo=resultado["nivel_riesgo"],
            medico_id=medico.id if medico else None,
        )
        db.add(prediccion)
        await db.flush()
        await db.refresh(prediccion)
        return prediccion

    @staticmethod
    async def ejecutar_para_paciente(
        db: AsyncSession,
        paciente_id: int,
        algoritmo: AlgoritmoS2 = "mejor",
        medico: Optional[Usuario] = None,
    ) -> dict:
        """Obtiene datos clínicos del paciente y ejecuta S-2 automáticamente."""
        paciente, dc = await PrediccionService._obtener_paciente_con_datos(db, paciente_id)
        datos_modelo = datos_clinicos_a_s2(paciente, dc)
        resultado = predecir_s2(datos_modelo, algoritmo=algoritmo)

        prediccion = await PrediccionService.guardar(
            db, paciente_id, datos_modelo, resultado, medico
        )
        await PrediccionService._generar_triage_automatico(
            db, paciente_id, prediccion.id, medico
        )

        return {
            "paciente_id":     paciente_id,
            "paciente_nombre": f"{paciente.nombre} {paciente.apellidos}",
            "prediccion_id":   prediccion.id,
            "datos_entrada":   datos_modelo,
            **resultado,
        }

    @staticmethod
    async def listar_por_paciente(db: AsyncSession, paciente_id: int) -> list[Prediccion]:
        result = await db.execute(
            select(Prediccion)
            .where(Prediccion.paciente_id == paciente_id)
            .order_by(Prediccion.fecha_prediccion.desc())
        )
        return list(result.scalars().all())
