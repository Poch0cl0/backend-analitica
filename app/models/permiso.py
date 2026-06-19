"""Permisos por rol."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.rol import Rol


class Permiso(Base):
    __tablename__ = "permisos"
    __table_args__ = (UniqueConstraint("rol_id", "modulo", "accion", name="uq_permiso_rol_modulo_accion"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    modulo: Mapped[str] = mapped_column(String(50), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)

    rol: Mapped["Rol"] = relationship(back_populates="permisos")
