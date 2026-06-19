"""Rol de usuario del sistema."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.permiso import Permiso
    from app.models.usuario import Usuario


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="rol")
    permisos: Mapped[List["Permiso"]] = relationship(back_populates="rol")
