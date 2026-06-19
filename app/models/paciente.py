"""Paciente."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cita import Cita
    from app.models.contacto import ContactoPaciente
    from app.models.datos_clinicos import DatosClinicos
    from app.models.prediccion import Prediccion
    from app.models.recomendacion import Recomendacion
    from app.models.triage import Triage
    from app.models.usuario import Usuario


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    telefono_principal: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    medico_asignado_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    medico_asignado: Mapped[Optional["Usuario"]] = relationship(back_populates="pacientes_asignados")
    datos_clinicos: Mapped[Optional["DatosClinicos"]] = relationship(
        back_populates="paciente", uselist=False
    )
    citas: Mapped[List["Cita"]] = relationship(back_populates="paciente")
    predicciones: Mapped[List["Prediccion"]] = relationship(back_populates="paciente")
    triages: Mapped[List["Triage"]] = relationship(back_populates="paciente")
    recomendaciones: Mapped[List["Recomendacion"]] = relationship(back_populates="paciente")
    contactos: Mapped[List["ContactoPaciente"]] = relationship(back_populates="paciente")
