"""Paciente service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.paciente import Paciente
from app.schemas.paciente import PacienteCreate, PacienteUpdate


class PacienteService:
    @staticmethod
    async def listar(db: AsyncSession, activo: bool | None = True) -> list[Paciente]:
        query = select(Paciente).options(selectinload(Paciente.medico_asignado))
        if activo is not None:
            query = query.where(Paciente.activo == activo)
        result = await db.execute(query.order_by(Paciente.apellidos, Paciente.nombre))
        return list(result.scalars().all())

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
        return paciente
