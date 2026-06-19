"""Datos clínicos del paciente."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente


class DatosClinicos(Base):
    __tablename__ = "datos_clinicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("pacientes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    edad_gestacional_semanas: Mapped[Optional[int]] = mapped_column(Integer)
    longitud_cervical_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    embarazo_multiple: Mapped[bool] = mapped_column(Boolean, default=False)
    parto_prematuro_previo: Mapped[bool] = mapped_column(Boolean, default=False)
    hipertension_gestacional: Mapped[bool] = mapped_column(Boolean, default=False)
    bmi: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    bmi_categoria: Mapped[Optional[str]] = mapped_column(String(30))
    num_condiciones_cronicas: Mapped[int] = mapped_column(Integer, default=0)
    infeccion_activa: Mapped[bool] = mapped_column(Boolean, default=False)
    diabetes_pregestacional: Mapped[bool] = mapped_column(Boolean, default=False)
    diabetes_gestacional: Mapped[bool] = mapped_column(Boolean, default=False)
    hipertension_cronica: Mapped[bool] = mapped_column(Boolean, default=False)
    eclampsia: Mapped[bool] = mapped_column(Boolean, default=False)
    hepatitis_b: Mapped[bool] = mapped_column(Boolean, default=False)
    hepatitis_c: Mapped[bool] = mapped_column(Boolean, default=False)
    sifilis: Mapped[bool] = mapped_column(Boolean, default=False)
    clamidia: Mapped[bool] = mapped_column(Boolean, default=False)
    gonorrea: Mapped[bool] = mapped_column(Boolean, default=False)
    cesareas_previas: Mapped[bool] = mapped_column(Boolean, default=False)
    num_cesareas: Mapped[int] = mapped_column(Integer, default=0)
    num_partos_previos_vivos: Mapped[int] = mapped_column(Integer, default=0)
    alerta_activa: Mapped[bool] = mapped_column(Boolean, default=False)
    notas_medicas: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    paciente: Mapped["Paciente"] = relationship(back_populates="datos_clinicos")
