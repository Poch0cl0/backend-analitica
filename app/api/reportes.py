"""Report export endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


@router.get("/paciente/{paciente_id}/export")
async def exportar_reporte_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("reportes", "exportar"))],
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
):
    content, media_type, filename = await ReporteService.exportar(db, paciente_id, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
