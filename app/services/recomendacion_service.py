"""Recomendación service (S-4)."""

import math
from datetime import date
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.ml_models.recomendaciones.predecir_s4 import predecir_recomendacion
from app.models.datos_clinicos import DatosClinicos
from app.models.intervencion import CatalogoIntervencion
from app.models.paciente import Paciente
from app.models.prediccion import Prediccion
from app.models.recomendacion import Recomendacion
from app.models.usuario import Usuario
from app.schemas.recomendacion import prioridad_a_num, prioridad_a_slug
from app.services.prediccion_service import datos_clinicos_a_s2

_ALGORITMOS = {
    "if_then": "recomendacion_if_then",
    "cart": "recomendacion_cart",
    "rf": "recomendacion_random_forest",
}


class RecomendacionService:
    @staticmethod
    def ejecutar_modelo(datos: dict) -> dict:
        return predecir_recomendacion(datos)

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
    async def guardar(
        db: AsyncSession,
        paciente_id: int,
        resultado: dict,
        prediccion_id: Optional[int] = None,
        medico_id: Optional[int] = None,
    ) -> list[Recomendacion]:
        guardadas: list[Recomendacion] = []
        for algoritmo, campo in _ALGORITMOS.items():
            codigo = resultado[campo]
            intervencion = await RecomendacionService._resolver_intervencion(db, codigo)
            rec = Recomendacion(
                paciente_id=paciente_id,
                prediccion_id=prediccion_id,
                intervencion_id=intervencion.id,
                algoritmo=algoritmo,
                titulo=intervencion.nombre,
                estado="activo",
                origen="s4_auto",
                es_manual=False,
                medico_id=medico_id,
            )
            db.add(rec)
            guardadas.append(rec)
            rec.intervencion = intervencion

        await db.flush()
        return guardadas

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

        campos_req = {
            "bmi": dc.bmi,
            "longitud_cervical_mm": dc.longitud_cervical_mm,
            "edad_gestacional_semanas": dc.edad_gestacional_semanas,
        }
        faltantes = [k for k, v in campos_req.items() if v is None]
        if faltantes:
            raise BadRequestError(
                f"Faltan datos clínicos obligatorios para S-4: {faltantes}"
            )

        datos_modelo = datos_clinicos_a_s2(paciente, dc)
        resultado_s4 = predecir_recomendacion(datos_modelo)
        medico_id = medico.id if medico else None
        guardadas = await RecomendacionService.guardar(
            db, paciente_id, resultado_s4, prediccion_id, medico_id=medico_id
        )

        prob = float(prediccion.prob_consenso) if prediccion.prob_consenso else None
        algoritmo = (
            prediccion.datos_entrada_snapshot.get("algoritmo_usado")
            if prediccion.datos_entrada_snapshot else None
        )

        recomendaciones_guardadas = [
            {
                "algoritmo": rec.algoritmo,
                "recomendacion": resultado_s4[_ALGORITMOS[rec.algoritmo]],
                "recomendacion_id": rec.id,
                "intervencion": rec.intervencion,
            }
            for rec in guardadas
        ]

        return {
            "paciente_id": paciente_id,
            "paciente_nombre": f"{paciente.nombre} {paciente.apellidos}",
            "prediccion_id": prediccion_id,
            "datos_entrada": datos_modelo,
            "prob_prematuro": prob,
            "algoritmo_s2": algoritmo,
            "entradas_s4": resultado_s4["entradas_s4"],
            "recomendacion_if_then": resultado_s4["recomendacion_if_then"],
            "recomendacion_cart": resultado_s4["recomendacion_cart"],
            "recomendacion_random_forest": resultado_s4["recomendacion_random_forest"],
            "importancia_variables_rf": resultado_s4["importancia_variables_rf"],
            "recomendaciones_guardadas": recomendaciones_guardadas,
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
