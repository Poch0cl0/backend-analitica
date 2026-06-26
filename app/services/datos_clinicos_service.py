"""Datos clínicos service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.datos_clinicos import DatosClinicos
from app.models.paciente import Paciente
from app.schemas.paciente import DatosClinicosCreate, DatosClinicosUpdate


CONDICIONES_CRONICAS = [
    "diabetes_pregestacional",
    "diabetes_gestacional",
    "hipertension_cronica",
    "hipertension_gestacional",
    "eclampsia",
]

INFECCIONES = [
    "gonorrea",
    "sifilis",
    "clamidia",
    "hepatitis_b",
    "hepatitis_c",
]


def _auto_computar(data: dict) -> dict:
    """Calcula num_condiciones_cronicas e infeccion_activa desde campos individuales."""
    result = dict(data)
    result["num_condiciones_cronicas"] = sum(1 for f in CONDICIONES_CRONICAS if data.get(f))
    result["infeccion_activa"] = any(data.get(f) for f in INFECCIONES)
    return result


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

        payload = _auto_computar(data.model_dump())
        datos = DatosClinicos(paciente_id=paciente_id, **payload)
        db.add(datos)
        await db.flush()
        await db.refresh(datos)
        return datos

    @staticmethod
    async def actualizar(
        db: AsyncSession, paciente_id: int, data: DatosClinicosUpdate
    ) -> DatosClinicos:
        datos = await DatosClinicosService.obtener(db, paciente_id)
        payload = _auto_computar(data.model_dump(exclude_unset=True))
        for key, value in payload.items():
            setattr(datos, key, value)
        await db.flush()
        await db.refresh(datos)
        return datos
