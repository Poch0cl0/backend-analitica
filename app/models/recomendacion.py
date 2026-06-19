"""Recomendaciones de intervención."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.intervencion import CatalogoIntervencion
    from app.models.paciente import Paciente
    from app.models.prediccion import Prediccion
    from app.models.usuario import Usuario


class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"))
    prediccion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("predicciones.id", ondelete="SET NULL")
    )
    intervencion_id: Mapped[int] = mapped_column(
        ForeignKey("catalogo_intervenciones.id", ondelete="RESTRICT")
    )
    algoritmo: Mapped[str] = mapped_column(String(30), nullable=False)
    prioridad: Mapped[Optional[int]] = mapped_column()
    confianza: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    titulo: Mapped[Optional[str]] = mapped_column(String(200))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    notas: Mapped[Optional[str]] = mapped_column(Text)
    fecha_revision: Mapped[Optional[date]] = mapped_column(Date)
    medico_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    es_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    origen: Mapped[str] = mapped_column(String(20), default="s4_auto")
    fecha_recomendacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    paciente: Mapped["Paciente"] = relationship(back_populates="recomendaciones")
    intervencion: Mapped["CatalogoIntervencion"] = relationship(back_populates="recomendaciones")
    medico: Mapped[Optional["Usuario"]] = relationship()
