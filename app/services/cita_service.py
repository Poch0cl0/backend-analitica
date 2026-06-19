"""Cita service."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.prediccion import Prediccion
from app.schemas.cita import CitaCreate, CitaUpdate, DisponibilidadSlot

HORARIO_INICIO = time(8, 0)
HORARIO_FIN = time(18, 0)
SLOT_MINUTOS = 30


class CitaService:
    @staticmethod
    async def _enriquecer(db: AsyncSession, cita: Cita) -> dict:
        result = await db.execute(
            select(Cita)
            .options(
                selectinload(Cita.paciente).selectinload(Paciente.datos_clinicos),
                selectinload(Cita.medico),
            )
            .where(Cita.id == cita.id)
        )
        c = result.scalar_one()
        dc = c.paciente.datos_clinicos if c.paciente else None
        pred = (
            await db.execute(
                select(Prediccion)
                .where(Prediccion.paciente_id == c.paciente_id)
                .order_by(Prediccion.fecha_prediccion.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return {
            "id": c.id,
            "paciente_id": c.paciente_id,
            "medico_id": c.medico_id,
            "fecha_hora": c.fecha_hora,
            "duracion_minutos": c.duracion_minutos,
            "estado": c.estado,
            "motivo": c.motivo,
            "notas": c.notas,
            "created_at": c.created_at,
            "paciente_nombre": f"{c.paciente.nombre} {c.paciente.apellidos}" if c.paciente else None,
            "paciente_dni": c.paciente.dni if c.paciente else None,
            "medico_nombre": f"{c.medico.nombre} {c.medico.apellidos}" if c.medico else None,
            "semanas_gestacion": dc.edad_gestacional_semanas if dc else None,
            "nivel_riesgo": pred.nivel_riesgo if pred else None,
        }

    @staticmethod
    async def listar(
        db: AsyncSession,
        fecha: date | None = None,
        medico_id: int | None = None,
        estado: str | None = None,
    ) -> list[Cita]:
        query = select(Cita)
        conditions = []
        if fecha:
            inicio = datetime.combine(fecha, time.min)
            fin = datetime.combine(fecha, time.max)
            conditions.append(and_(Cita.fecha_hora >= inicio, Cita.fecha_hora <= fin))
        if medico_id:
            conditions.append(Cita.medico_id == medico_id)
        if estado:
            conditions.append(Cita.estado == estado)
        if conditions:
            query = query.where(and_(*conditions))
        result = await db.execute(query.order_by(Cita.fecha_hora))
        citas = list(result.scalars().all())
        enriched = []
        for cita in citas:
            enriched.append(await CitaService._enriquecer(db, cita))
        return enriched

    @staticmethod
    async def crear(db: AsyncSession, data: CitaCreate) -> Cita:
        conflict = await db.execute(
            select(Cita).where(
                Cita.medico_id == data.medico_id,
                Cita.fecha_hora == data.fecha_hora,
                Cita.estado != "cancelada",
            )
        )
        if conflict.scalar_one_or_none():
            raise BadRequestError("El médico ya tiene una cita en ese horario")

        cita = Cita(**data.model_dump())
        db.add(cita)
        await db.flush()
        await db.refresh(cita)
        return cita

    @staticmethod
    async def obtener(db: AsyncSession, cita_id: int) -> Cita:
        cita = await db.get(Cita, cita_id)
        if cita is None:
            raise NotFoundError("Cita no encontrada")
        return cita

    @staticmethod
    async def cambiar_estado(db: AsyncSession, cita_id: int, estado: str) -> Cita:
        cita = await CitaService.obtener(db, cita_id)
        transiciones = {
            "programada": {"en_atencion", "cancelada"},
            "en_atencion": {"cumplida", "cancelada"},
            "cumplida": set(),
            "cancelada": set(),
        }
        if estado not in transiciones.get(cita.estado, set()):
            raise BadRequestError(
                f"No se puede cambiar de '{cita.estado}' a '{estado}'"
            )
        cita.estado = estado
        await db.flush()
        await db.refresh(cita)
        return cita

    @staticmethod
    async def actualizar(db: AsyncSession, cita_id: int, data: CitaUpdate) -> dict:
        cita = await CitaService.obtener(db, cita_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(cita, key, value)
        await db.flush()
        return await CitaService._enriquecer(db, cita)

    @staticmethod
    async def obtener_enriquecida(db: AsyncSession, cita_id: int) -> dict:
        cita = await CitaService.obtener(db, cita_id)
        return await CitaService._enriquecer(db, cita)

    @staticmethod
    async def cancelar(db: AsyncSession, cita_id: int) -> Cita:
        return await CitaService.cambiar_estado(db, cita_id, "cancelada")

    @staticmethod
    async def disponibilidad(
        db: AsyncSession, medico_id: int, fecha: date
    ) -> list[DisponibilidadSlot]:
        inicio_dia = datetime.combine(fecha, HORARIO_INICIO)
        fin_dia = datetime.combine(fecha, HORARIO_FIN)

        result = await db.execute(
            select(Cita).where(
                Cita.medico_id == medico_id,
                Cita.fecha_hora >= inicio_dia,
                Cita.fecha_hora < fin_dia,
                Cita.estado != "cancelada",
            )
        )
        ocupadas = {c.fecha_hora for c in result.scalars().all()}

        slots: list[DisponibilidadSlot] = []
        current = inicio_dia
        while current + timedelta(minutes=SLOT_MINUTOS) <= fin_dia:
            slot_fin = current + timedelta(minutes=SLOT_MINUTOS)
            slots.append(
                DisponibilidadSlot(
                    hora_inicio=current.strftime("%H:%M"),
                    hora_fin=slot_fin.strftime("%H:%M"),
                    disponible=current not in ocupadas,
                )
            )
            current = slot_fin
        return slots
