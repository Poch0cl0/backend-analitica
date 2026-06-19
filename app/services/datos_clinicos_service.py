"""Datos clínicos service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.datos_clinicos import DatosClinicos
from app.models.paciente import Paciente
from app.schemas.paciente import DatosClinicosCreate, DatosClinicosUpdate


class DatosClinicosService:
    @staticmethod
    async def obtener(db: AsyncSession, paciente_id: int) -> DatosClinicos:
        result = await db.execute(
            select(DatosClinicos).where(DatosClinicos.paciente_id == paciente_id)
        )
        datos = result.scalar_one_or_none()
        if datos is None:
            raise NotFoundError("Datos clínicos no encontrados para este paciente")
        return datos

    @staticmethod
    async def crear(db: AsyncSession, paciente_id: int, data: DatosClinicosCreate) -> DatosClinicos:
        paciente = await db.get(Paciente, paciente_id)
        if paciente is None:
            raise NotFoundError("Paciente no encontrado")

        existing = await db.execute(
            select(DatosClinicos).where(DatosClinicos.paciente_id == paciente_id)
        )
        if existing.scalar_one_or_none():
            raise BadRequestError("El paciente ya tiene datos clínicos registrados")

        datos = DatosClinicos(paciente_id=paciente_id, **data.model_dump())
        db.add(datos)
        await db.flush()
        await db.refresh(datos)
        return datos

    @staticmethod
    async def actualizar(
        db: AsyncSession, paciente_id: int, data: DatosClinicosUpdate
    ) -> DatosClinicos:
        datos = await DatosClinicosService.obtener(db, paciente_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(datos, key, value)
        await db.flush()
        await db.refresh(datos)
        return datos
