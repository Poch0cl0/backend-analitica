"""Usuario del sistema."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.auditoria import Auditoria
    from app.models.cita import Cita
    from app.models.paciente import Paciente
    from app.models.prediccion import Prediccion
    from app.models.prediccion_feedback import PrediccionFeedback
    from app.models.rol import Rol


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")
    pacientes_asignados: Mapped[List["Paciente"]] = relationship(back_populates="medico_asignado")
    citas: Mapped[List["Cita"]] = relationship(back_populates="medico")
    predicciones: Mapped[List["Prediccion"]] = relationship(back_populates="medico")
    feedbacks: Mapped[List["PrediccionFeedback"]] = relationship(back_populates="medico")
    auditorias: Mapped[List["Auditoria"]] = relationship(back_populates="usuario")
