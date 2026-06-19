"""Recomendación service (S-3 recomendaciones — placeholder para integración futura)."""

from sqlalchemy.ext.asyncio import AsyncSession


class RecomendacionService:
    @staticmethod
    async def generar(db: AsyncSession, paciente_id: int, prediccion_id: int | None = None) -> list:
        """Genera recomendaciones usando CART, IF-THEN y RF."""
        # Integración futura con app/ml_models/recomendaciones/
        return []
