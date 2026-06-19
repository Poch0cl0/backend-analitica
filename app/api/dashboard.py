"""Dashboard endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.dashboard import DashboardResumen
from app.services.dashboard_service import DashboardService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/resumen", response_model=DashboardResumen)
async def obtener_resumen(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    return await DashboardService.resumen(db)
