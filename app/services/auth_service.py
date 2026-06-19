"""Authentication service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.usuario import Usuario


class AuthService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Usuario | None:
        result = await db.execute(
            select(Usuario)
            .options(selectinload(Usuario.rol))
            .where(Usuario.id == user_id, Usuario.activo.is_(True))
        )
        return result.scalar_one_or_none()
