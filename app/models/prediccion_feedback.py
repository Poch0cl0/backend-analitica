"""Feedback de médicos sobre predicciones."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.prediccion import Prediccion
    from app.models.usuario import Usuario


class PrediccionFeedback(Base):
    __tablename__ = "prediccion_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediccion_id: Mapped[int] = mapped_column(
        ForeignKey("predicciones.id", ondelete="CASCADE")
    )
    medico_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    modelo: Mapped[Optional[str]] = mapped_column(String(50))
    voto_correcta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prediccion: Mapped["Prediccion"] = relationship(back_populates="feedbacks")
    medico: Mapped["Usuario"] = relationship(back_populates="feedbacks")
