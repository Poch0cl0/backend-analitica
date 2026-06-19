"""Contactos con pacientes."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.usuario import Usuario


class ContactoPaciente(Base):
    __tablename__ = "contactos_paciente"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    nota: Mapped[str] = mapped_column(Text, nullable=False)
    medico_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    paciente: Mapped["Paciente"] = relationship(back_populates="contactos")
    medico: Mapped[Optional["Usuario"]] = relationship()
