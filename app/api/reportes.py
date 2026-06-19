"""Report export endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


class EnviarReporteResponse(BaseModel):
    enviado: bool
    email: str
    tipo: str
    mensaje: str


@router.get("/paciente/{paciente_id}/export")
async def exportar_reporte_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("reportes", "exportar"))],
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    tipo: Literal["completo", "prediccion", "triaje"] = Query("completo"),
):
    try:
        if format == "pdf":
            content = await ReporteService.generar_pdf(db, paciente_id, tipo=tipo)
            filename = f"reporte_{tipo}.pdf"
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        content, media_type, filename = await ReporteService.exportar(db, paciente_id, format)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc


@router.post(
    "/paciente/{paciente_id}/enviar",
    response_model=EnviarReporteResponse,
    summary="Enviar reporte al correo registrado de la paciente",
)
async def enviar_reporte_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("reportes", "exportar"))],
    tipo: Literal["completo", "prediccion", "triaje"] = Query("prediccion"),
):
    try:
        return await ReporteService.enviar_por_correo(db, paciente_id, tipo=tipo)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar correo: {exc}",
        ) from exc
