"""Paciente service."""

import math
from typing import Optional

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.paciente import Paciente
from app.schemas.paciente import PacienteCreate, PacienteUpdate


class PacienteService:
    @staticmethod
    async def listar(
        db: AsyncSession,
        *,
        q: str | None = None,
        estado: str | None = None,
        medico_id: int | None = None,
        mes_registro: int | None = None,
        page: int = 1,
        limit: int = 20,
        activo: bool | None = True,
    ) -> dict:
        query = select(Paciente).options(selectinload(Paciente.medico_asignado))

        # El filtro de activo/inactivo lo controla `estado` cuando corresponde;
        # de lo contrario se usa el parámetro `activo`.
        if estado == "inactivo":
            query = query.where(Paciente.activo.is_(False))
        elif estado == "activo":
            query = query.where(Paciente.activo.is_(True))
        elif estado == "sin_medico":
            query = query.where(Paciente.medico_asignado_id.is_(None))
            if activo is not None:
                query = query.where(Paciente.activo == activo)
        else:
            if activo is not None:
                query = query.where(Paciente.activo == activo)

        if q:
            like = f"%{q}%"
            query = query.where(
                or_(
                    Paciente.nombre.ilike(like),
                    Paciente.apellidos.ilike(like),
                    Paciente.dni.ilike(like),
                )
            )
        if medico_id:
            query = query.where(Paciente.medico_asignado_id == medico_id)
        if mes_registro:
            query = query.where(func.extract("month", Paciente.created_at) == mes_registro)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar() or 0
        pages = max(1, math.ceil(total / limit))

        result = await db.execute(
            query.order_by(Paciente.apellidos, Paciente.nombre)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return {
            "items": list(result.scalars().all()),
            "total": total,
            "page": page,
            "pages": pages,
        }

    @staticmethod
    async def listar_simple(db: AsyncSession, activo: bool | None = True) -> list[Paciente]:
        data = await PacienteService.listar(db, activo=activo, page=1, limit=10000)
        return data["items"]

    @staticmethod
    async def obtener(db: AsyncSession, paciente_id: int) -> Paciente:
        result = await db.execute(
            select(Paciente)
            .options(selectinload(Paciente.medico_asignado), selectinload(Paciente.datos_clinicos))
            .where(Paciente.id == paciente_id)
        )
        paciente = result.scalar_one_or_none()
        if paciente is None:
            raise NotFoundError("Paciente no encontrado")
        return paciente

    @staticmethod
    async def obtener_perfil(db: AsyncSession, paciente_id: int) -> dict | None:
        result = await db.execute(
            text("SELECT * FROM vista_perfil_completo WHERE id = :id"),
            {"id": paciente_id},
        )
        row = result.mappings().first()
        if row is None:
            raise NotFoundError("Paciente no encontrado")
        data = dict(row)
        medico_nombre = None
        if data.get("medico_nombre") and data.get("medico_apellidos"):
            medico_nombre = f"{data['medico_nombre']} {data['medico_apellidos']}"
        return {
            "id": data["id"],
            "dni": data["dni"],
            "nombre": data["nombre"],
            "apellidos": data["apellidos"],
            "telefono_principal": data.get("telefono_principal"),
            "email": data.get("email"),
            "edad_madre": data.get("edad_madre"),
            "edad_gestacional_semanas": data.get("edad_gestacional_semanas"),
            "longitud_cervical_mm": data.get("longitud_cervical_mm"),
            "embarazo_multiple": data.get("embarazo_multiple"),
            "parto_prematuro_previo": data.get("parto_prematuro_previo"),
            "hipertension_gestacional": data.get("hipertension_gestacional"),
            "bmi": data.get("bmi"),
            "num_condiciones_cronicas": data.get("num_condiciones_cronicas"),
            "infeccion_activa": data.get("infeccion_activa"),
            "prob_consenso": data.get("prob_consenso"),
            "nivel_riesgo": data.get("nivel_riesgo"),
            "semanas_estimadas_consenso": data.get("semanas_estimadas_consenso"),
            "nivel_urgencia": data.get("nivel_urgencia"),
            "medico_nombre": medico_nombre,
            "fecha_ultima_prediccion": data.get("fecha_ultima_prediccion"),
            "fecha_ultimo_triage": data.get("fecha_ultimo_triage"),
        }

    @staticmethod
    async def crear(db: AsyncSession, data: PacienteCreate) -> Paciente:
        paciente = Paciente(**data.model_dump())
        db.add(paciente)
        await db.flush()
        await db.refresh(paciente)
        return paciente

    @staticmethod
    async def actualizar(db: AsyncSession, paciente_id: int, data: PacienteUpdate) -> Paciente:
        paciente = await PacienteService.obtener(db, paciente_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(paciente, key, value)
        await db.flush()
        await db.refresh(paciente)
        return paciente

    @staticmethod
    async def desactivar(db: AsyncSession, paciente_id: int) -> Paciente:
        paciente = await PacienteService.obtener(db, paciente_id)
        paciente.activo = False
        await db.flush()
        await db.refresh(paciente)
        return paciente
