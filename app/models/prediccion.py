"""Predicciones ML."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.triage import Triage
    from app.models.usuario import Usuario


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"))
    datos_entrada_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fecha_prediccion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prob_random_forest: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    semanas_estimadas_rf: Mapped[Optional[int]] = mapped_column(Integer)
    prob_catboost: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    semanas_estimadas_cb: Mapped[Optional[int]] = mapped_column(Integer)
    prob_logistica: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    semanas_estimadas_logistica: Mapped[Optional[int]] = mapped_column(Integer)

    prob_consenso: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    semanas_estimadas_consenso: Mapped[Optional[int]] = mapped_column(Integer)
    nivel_riesgo: Mapped[Optional[str]] = mapped_column(String(10))
    shap_values: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    medico_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    paciente: Mapped["Paciente"] = relationship(back_populates="predicciones")
    medico: Mapped[Optional["Usuario"]] = relationship(back_populates="predicciones")
    triages: Mapped[list["Triage"]] = relationship(back_populates="prediccion")
