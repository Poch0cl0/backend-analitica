"""Contacto service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.contacto import ContactoPaciente
from app.models.paciente import Paciente
from app.models.usuario import Usuario


class ContactoService:
    @staticmethod
    async def listar(db: AsyncSession, paciente_id: int) -> list[ContactoPaciente]:
        result = await db.execute(
            select(ContactoPaciente)
            .where(ContactoPaciente.paciente_id == paciente_id)
            .order_by(ContactoPaciente.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def crear(
        db: AsyncSession,
        paciente_id: int,
        tipo: str,
        nota: str,
        medico: Usuario | None = None,
    ) -> ContactoPaciente:
        paciente = await db.get(Paciente, paciente_id)
        if paciente is None:
            raise NotFoundError("Paciente no encontrado")

        contacto = ContactoPaciente(
            paciente_id=paciente_id,
            tipo=tipo,
            nota=nota,
            medico_id=medico.id if medico else None,
        )
        db.add(contacto)
        await db.flush()
        await db.refresh(contacto)
        return contacto
