"""Recomendación service (S-4) — powered by Gemini API."""

import math
from datetime import date
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.datos_clinicos import DatosClinicos
from app.models.intervencion import CatalogoIntervencion
from app.models.paciente import Paciente
from app.models.prediccion import Prediccion
from app.models.recomendacion import Recomendacion
from app.models.triage import Triage
from app.models.usuario import Usuario
from app.schemas.recomendacion import prioridad_a_num, prioridad_a_slug
from app.services.gemini_service import GeminiService


class RecomendacionService:

    @staticmethod
    def _fallback_recomendacion(
        prob_prematuro: Optional[float] = None,
        nivel_urgencia: str = "VERDE",
        parto_prematuro_previo: bool = False,
        num_condiciones_cronicas: int = 0,
        longitud_cervical_mm: Optional[float] = None,
        infeccion_activa: bool = False,
        embarazo_multiple: bool = False,
    ) -> dict:
        prob = prob_prematuro if prob_prematuro is not None else 0.0
        urg = nivel_urgencia.upper() if nivel_urgencia else "VERDE"
        lc = longitud_cervical_mm if longitud_cervical_mm is not None else 999

        if urg == "ROJO" or prob >= 0.60:
            slug = "derivacion_alto_riesgo"
            titulo = "Derivación a unidad de alto riesgo obstétrico"
            desc = "Paciente con riesgo crítico de parto prematuro que requiere atención especializada inmediata."
        elif infeccion_activa:
            slug = "tratar_infeccion"
            titulo = "Tratamiento de infección activa"
            desc = "Presencia de infección activa que requiere tratamiento antibiótico oportuno para reducir riesgo obstétrico."
        elif parto_prematuro_previo and lc < 25:
            slug = "progesterona_vaginal"
            titulo = "Progesterona vaginal"
            desc = "Antecedente de parto prematuro previo combinado con longitud cervical corta. Indicar progesterona vaginal."
        elif lc < 25:
            slug = "seguimiento_estrecho_lc"
            titulo = "Seguimiento estrecho por longitud cervical corta"
            desc = "Longitud cervical por debajo de 25 mm. Requiere monitoreo ecográfico frecuente."
        elif urg == "NARANJA" or num_condiciones_cronicas >= 3 or embarazo_multiple:
            slug = "vigilancia_hta_multiple"
            titulo = "Vigilancia de hipertensión o embarazo múltiple"
            desc = "Paciente con factores que requieren control prenatal más frecuente y evaluación de riesgo cardiovascular."
        elif prob >= 0.25 or urg == "AMARILLO":
            slug = "seguimiento_estrecho_lc"
            titulo = "Seguimiento estrecho"
            desc = "Riesgo moderado de parto prematuro. Incrementar frecuencia de controles prenatales."
        else:
            slug = "control_prenatal_rutinario"
            titulo = "Control prenatal rutinario"
            desc = "Paciente de bajo riesgo. Continuar con controles prenatales estándar según guías locales."

        return {"recomendacion": slug, "titulo": titulo, "descripcion": desc}

    @staticmethod
    def ejecutar_modelo(datos: dict) -> dict:
        """Endpoint legacy S-4."""
        slug = RecomendacionService._fallback_recomendacion(
            prob_prematuro=datos.get("prob_prematuro"),
            nivel_urgencia=datos.get("nivel_urgencia", "VERDE"),
            parto_prematuro_previo=bool(datos.get("parto_prematuro_previo", False)),
            num_condiciones_cronicas=int(datos.get("num_condiciones_cronicas", 0)),
            longitud_cervical_mm=datos.get("cl_sim_mm"),
            infeccion_activa=bool(datos.get("infeccion_activa", False)),
            embarazo_multiple=bool(datos.get("embarazo_multiple", False)),
        )["recomendacion"]
        return {
            "entradas_s4": datos,
            "recomendacion_if_then": slug,
            "recomendacion_cart": slug,
            "recomendacion_random_forest": slug,
            "importancia_variables_rf": [],
            "recomendaciones_posibles": [],
        }

    @staticmethod
    async def _resolver_intervencion(db: AsyncSession, codigo: str) -> CatalogoIntervencion:
        result = await db.execute(
            select(CatalogoIntervencion).where(
                CatalogoIntervencion.codigo == codigo,
                CatalogoIntervencion.activo.is_(True),
            )
        )
        intervencion = result.scalar_one_or_none()
        if intervencion is None:
            raise BadRequestError(
                f"No existe intervención activa con código '{codigo}' en el catálogo."
            )
        return intervencion

    @staticmethod
    async def guardar_gemini(
        db: AsyncSession,
        paciente_id: int,
        slug: str,
        titulo: str,
        descripcion: str,
        prediccion_id: Optional[int] = None,
        medico_id: Optional[int] = None,
    ) -> Recomendacion:
        intervencion = await RecomendacionService._resolver_intervencion(db, slug)
        rec = Recomendacion(
            paciente_id=paciente_id,
            prediccion_id=prediccion_id,
            intervencion_id=intervencion.id,
            algoritmo="gemini",
            titulo=titulo or intervencion.nombre,
            descripcion=descripcion,
            estado="activo",
            origen="gemini",
            es_manual=False,
            medico_id=medico_id,
        )
        db.add(rec)
        await db.flush()
        await db.refresh(rec, attribute_names=["intervencion"])
        return rec

    @staticmethod
    async def ejecutar_para_paciente(
        db: AsyncSession,
        paciente_id: int,
        prediccion_id: int,
        medico: Optional[Usuario] = None,
    ) -> dict:
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
                "Registre los datos clínicos antes de generar recomendaciones."
            )

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

        prob_consenso = float(prediccion.prob_consenso) if prediccion.prob_consenso else None

        triage_result = await db.execute(
            select(Triage).where(
                Triage.paciente_id == paciente_id,
                Triage.prediccion_id == prediccion_id,
            ).order_by(Triage.fecha_triage.desc()).limit(1)
        )
        triage = triage_result.scalar_one_or_none()
        nivel_urgencia = triage.nivel_urgencia if triage else "VERDE"

        parto_previo = bool(dc.parto_prematuro_previo)
        cronicas = int(dc.num_condiciones_cronicas or 0)
        bmi_val = float(dc.bmi) if dc.bmi else None
        lc_val = float(dc.longitud_cervical_mm) if dc.longitud_cervical_mm else None
        infeccion = bool(dc.infeccion_activa)
        multi = int(dc.embarazo_multiple or 1) > 1

        try:
            gemini_result = GeminiService.generar_recomendacion(
                prob_prematuro=prob_consenso,
                nivel_urgencia=nivel_urgencia,
                parto_prematuro_previo=parto_previo,
                num_condiciones_cronicas=cronicas,
                bmi=bmi_val,
                longitud_cervical_mm=lc_val,
                infeccion_activa=infeccion,
                embarazo_multiple=multi,
            )
        except Exception:
            gemini_result = RecomendacionService._fallback_recomendacion(
                prob_prematuro=prob_consenso,
                nivel_urgencia=nivel_urgencia,
                parto_prematuro_previo=parto_previo,
                num_condiciones_cronicas=cronicas,
                longitud_cervical_mm=lc_val,
                infeccion_activa=infeccion,
                embarazo_multiple=multi,
            )

        medico_id = medico.id if medico else None
        rec = await RecomendacionService.guardar_gemini(
            db,
            paciente_id,
            gemini_result["recomendacion"],
            gemini_result["titulo"],
            gemini_result["descripcion"],
            prediccion_id=prediccion_id,
            medico_id=medico_id,
        )

        return {
            "paciente_id": paciente_id,
            "paciente_nombre": f"{paciente.nombre} {paciente.apellidos}",
            "prediccion_id": prediccion_id,
            "prob_prematuro": prob_consenso,
            "nivel_urgencia": nivel_urgencia,
            "recomendacion_gemini": {
                "recomendacion_id": rec.id,
                "recomendacion": gemini_result["recomendacion"],
                "titulo": rec.titulo,
                "descripcion": rec.descripcion,
                "intervencion": rec.intervencion,
            },
        }

    @staticmethod
    def _a_list_item(rec: Recomendacion, paciente: Paciente, dc: DatosClinicos | None, medico: Usuario | None) -> dict:
        titulo = rec.titulo or (rec.intervencion.nombre if rec.intervencion else "")
        fecha = rec.fecha_revision or rec.fecha_recomendacion.date()
        return {
            "id": rec.id,
            "paciente_nombre": f"{paciente.nombre} {paciente.apellidos}",
            "semanas_gestacion": dc.edad_gestacional_semanas if dc else None,
            "titulo": titulo,
            "tipo": rec.intervencion.categoria if rec.intervencion else None,
            "prioridad": prioridad_a_slug(rec.prioridad),
            "estado": rec.estado,
            "fecha": fecha,
            "medico_nombre": f"{medico.nombre} {medico.apellidos}" if medico else None,
        }

    @staticmethod
    async def listar(
        db: AsyncSession,
        *,
        tipo: str | None = None,
        prioridad: str | None = None,
        estado: str | None = None,
        medico_id: int | None = None,
        fecha: date | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        query = (
            select(Recomendacion)
            .join(Paciente, Recomendacion.paciente_id == Paciente.id)
            .join(CatalogoIntervencion, Recomendacion.intervencion_id == CatalogoIntervencion.id)
            .options(
                selectinload(Recomendacion.intervencion),
                selectinload(Recomendacion.paciente).selectinload(Paciente.datos_clinicos),
                selectinload(Recomendacion.medico),
            )
            .where(Recomendacion.estado != "cancelada")
        )
        if tipo:
            query = query.where(CatalogoIntervencion.categoria == tipo)
        if prioridad:
            query = query.where(Recomendacion.prioridad == prioridad_a_num(prioridad))
        if estado:
            query = query.where(Recomendacion.estado == estado)
        if medico_id:
            query = query.where(Recomendacion.medico_id == medico_id)
        if fecha:
            query = query.where(func.date(Recomendacion.fecha_recomendacion) == fecha)

        count_result = await db.execute(select(func.count(Recomendacion.id)).select_from(query.subquery()))
        total = count_result.scalar() or 0
        pages = max(1, math.ceil(total / limit))

        result = await db.execute(
            query.order_by(Recomendacion.fecha_recomendacion.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = []
        for rec in result.scalars().all():
            items.append(
                RecomendacionService._a_list_item(
                    rec, rec.paciente, rec.paciente.datos_clinicos, rec.medico
                )
            )
        return {"items": items, "total": total, "page": page, "pages": pages}

    @staticmethod
    async def obtener(db: AsyncSession, recomendacion_id: int) -> Recomendacion:
        result = await db.execute(
            select(Recomendacion)
            .options(selectinload(Recomendacion.intervencion))
            .where(Recomendacion.id == recomendacion_id)
        )
        rec = result.scalar_one_or_none()
        if rec is None:
            raise NotFoundError("Recomendación no encontrada")
        return rec

    @staticmethod
    async def crear_manual(
        db: AsyncSession,
        data: dict,
        medico: Optional[Usuario] = None,
    ) -> Recomendacion:
        intervencion = await db.get(CatalogoIntervencion, data["intervencion_id"])
        if intervencion is None or not intervencion.activo:
            raise BadRequestError("Intervención no válida")

        paciente = await db.get(Paciente, data["paciente_id"])
        if paciente is None or not paciente.activo:
            raise NotFoundError("Paciente no encontrado")

        rec = Recomendacion(
            paciente_id=data["paciente_id"],
            intervencion_id=data["intervencion_id"],
            algoritmo="manual",
            titulo=data["titulo"],
            descripcion=data.get("descripcion"),
            notas=data.get("notas"),
            fecha_revision=data.get("fecha_revision"),
            prioridad=prioridad_a_num(data.get("prioridad", "media")),
            estado="activo",
            es_manual=True,
            origen="manual",
            medico_id=medico.id if medico else None,
        )
        db.add(rec)
        await db.flush()
        await db.refresh(rec, attribute_names=["intervencion"])
        return rec

    @staticmethod
    async def actualizar(db: AsyncSession, recomendacion_id: int, data: dict) -> Recomendacion:
        rec = await RecomendacionService.obtener(db, recomendacion_id)
        if data.get("estado"):
            rec.estado = data["estado"]
        if data.get("prioridad"):
            rec.prioridad = prioridad_a_num(data["prioridad"])
        if "notas" in data and data["notas"] is not None:
            rec.notas = data["notas"]
        if "fecha_revision" in data:
            rec.fecha_revision = data["fecha_revision"]
        if data.get("titulo"):
            rec.titulo = data["titulo"]
        if "descripcion" in data:
            rec.descripcion = data["descripcion"]
        await db.flush()
        await db.refresh(rec, attribute_names=["intervencion"])
        return rec

    @staticmethod
    async def eliminar(db: AsyncSession, recomendacion_id: int) -> Recomendacion:
        rec = await RecomendacionService.obtener(db, recomendacion_id)
        rec.estado = "cancelada"
        await db.flush()
        return rec

    @staticmethod
    async def listar_por_paciente(
        db: AsyncSession,
        paciente_id: int,
    ) -> list[Recomendacion]:
        result = await db.execute(
            select(Recomendacion)
            .options(selectinload(Recomendacion.intervencion))
            .where(Recomendacion.paciente_id == paciente_id, Recomendacion.estado != "cancelada")
            .order_by(Recomendacion.fecha_recomendacion.desc(), Recomendacion.id.desc())
        )
        return list(result.scalars().all())
