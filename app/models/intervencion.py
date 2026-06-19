"""Catálogo de intervenciones clínicas."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.recomendacion import Recomendacion


class CatalogoIntervencion(Base):
    __tablename__ = "catalogo_intervenciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    categoria: Mapped[Optional[str]] = mapped_column(String(50))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    recomendaciones: Mapped[List["Recomendacion"]] = relationship(back_populates="intervencion")
