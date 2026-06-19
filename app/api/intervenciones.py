"""Catálogo de intervenciones."""

from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.intervencion import CatalogoIntervencion
from app.models.usuario import Usuario
from app.schemas.recomendacion import IntervencionResumen

router = APIRouter(prefix="/api/intervenciones", tags=["intervenciones"])


@router.get("", response_model=List[IntervencionResumen])
async def listar_intervenciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "leer"))],
):
    result = await db.execute(
        select(CatalogoIntervencion)
        .where(CatalogoIntervencion.activo.is_(True))
        .order_by(CatalogoIntervencion.nombre)
    )
    return list(result.scalars().all())
