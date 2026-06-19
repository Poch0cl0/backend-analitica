"""Citas médicas."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.usuario import Usuario


class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"))
    medico_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(default=30)
    estado: Mapped[str] = mapped_column(
        String(20), default="programada", nullable=False
    )  # programada, en_atencion, cumplida, cancelada
    motivo: Mapped[Optional[str]] = mapped_column(String(255))
    notas: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    paciente: Mapped["Paciente"] = relationship(back_populates="citas")
    medico: Mapped["Usuario"] = relationship(back_populates="citas")
