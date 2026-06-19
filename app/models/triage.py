"""Triage / priorización por urgencia (S-3)."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.prediccion import Prediccion


class Triage(Base):
    __tablename__ = "triage"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"))
    prediccion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("predicciones.id", ondelete="SET NULL")
    )
    nivel_urgencia: Mapped[str] = mapped_column(String(10), nullable=False)
    score_formula_ponderada: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    urgencia_arbol: Mapped[Optional[str]] = mapped_column(String(10))
    urgencia_ordinal: Mapped[Optional[str]] = mapped_column(String(10))
    factores_activos_detalle: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    acciones_urgentes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    fecha_triage: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    paciente: Mapped["Paciente"] = relationship(back_populates="triages")
    prediccion: Mapped[Optional["Prediccion"]] = relationship(back_populates="triages")
