"""Usuario service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    @staticmethod
    async def listar(db: AsyncSession) -> list[Usuario]:
        result = await db.execute(
            select(Usuario).options(selectinload(Usuario.rol)).order_by(Usuario.apellidos)
        )
        return list(result.scalars().all())

    @staticmethod
    async def obtener(db: AsyncSession, usuario_id: int) -> Usuario:
        result = await db.execute(
            select(Usuario)
            .options(selectinload(Usuario.rol))
            .where(Usuario.id == usuario_id)
        )
        usuario = result.scalar_one_or_none()
        if usuario is None:
            raise NotFoundError("Usuario no encontrado")
        return usuario

    @staticmethod
    async def crear(db: AsyncSession, data: UsuarioCreate) -> Usuario:
        datos = data.model_dump()
        password = datos.pop("password")
        datos["password_hash"] = hash_password(password)
        usuario = Usuario(**datos)
        db.add(usuario)
        await db.flush()
        await db.refresh(usuario, attribute_names=["rol"])
        return usuario

    @staticmethod
    async def actualizar(db: AsyncSession, usuario_id: int, data: UsuarioUpdate) -> Usuario:
        usuario = await UsuarioService.obtener(db, usuario_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(usuario, key, value)
        await db.flush()
        await db.refresh(usuario, attribute_names=["rol"])
        return usuario

    @staticmethod
    async def desactivar(db: AsyncSession, usuario_id: int) -> Usuario:
        usuario = await UsuarioService.obtener(db, usuario_id)
        usuario.activo = False
        await db.flush()
        return usuario
