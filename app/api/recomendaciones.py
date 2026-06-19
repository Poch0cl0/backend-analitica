"""Recomendaciones endpoints."""

from datetime import date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.recomendacion import (
    RecomendacionEjecutadaResponse,
    RecomendacionListResponse,
    RecomendacionManualCreate,
    RecomendacionResponse,
    RecomendacionUpdate,
)
from app.services.recomendacion_service import RecomendacionService

router = APIRouter(prefix="/api/recomendaciones", tags=["recomendaciones"])


@router.get("", response_model=RecomendacionListResponse)
async def listar_recomendaciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "leer"))],
    tipo: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    medico_id: Optional[int] = Query(None),
    fecha: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return await RecomendacionService.listar(
        db,
        tipo=tipo,
        prioridad=prioridad,
        estado=estado,
        medico_id=medico_id,
        fecha=fecha,
        page=page,
        limit=limit,
    )


@router.get("/export")
async def exportar_recomendaciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "leer"))],
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
):
    import io
    import csv

    data = await RecomendacionService.listar(db, page=1, limit=10000)
    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["id", "paciente_nombre", "titulo", "tipo", "prioridad", "estado", "fecha", "medico_nombre"],
        )
        writer.writeheader()
        for row in data["items"]:
            writer.writerow(row)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="recomendaciones.csv"'},
        )

    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=503, detail="openpyxl no instalado para exportar xlsx") from None

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Recomendaciones"
    headers = ["id", "paciente_nombre", "titulo", "tipo", "prioridad", "estado", "fecha", "medico_nombre"]
    ws.append(headers)
    for row in data["items"]:
        ws.append([row.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="recomendaciones.xlsx"'},
    )


@router.get("/paciente/{paciente_id}", response_model=List[RecomendacionResponse])
async def listar_recomendaciones_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "leer"))],
):
    return await RecomendacionService.listar_por_paciente(db, paciente_id)


@router.get("/{recomendacion_id}", response_model=RecomendacionResponse)
async def obtener_recomendacion(
    recomendacion_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "leer"))],
):
    try:
        return await RecomendacionService.obtener(db, recomendacion_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail) from exc


@router.post(
    "/ejecutar/{paciente_id}/{prediccion_id}",
    response_model=RecomendacionEjecutadaResponse,
)
async def ejecutar_recomendaciones_paciente(
    paciente_id: int,
    prediccion_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "ejecutar"))],
):
    try:
        return await RecomendacionService.ejecutar_para_paciente(
            db, paciente_id, prediccion_id=prediccion_id, medico=usuario
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/manual", response_model=RecomendacionResponse, status_code=201)
async def crear_recomendacion_manual(
    data: RecomendacionManualCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "ejecutar"))],
):
    try:
        return await RecomendacionService.crear_manual(db, data.model_dump(), medico=usuario)
    except (NotFoundError, BadRequestError) as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc


@router.put("/{recomendacion_id}", response_model=RecomendacionResponse)
async def actualizar_recomendacion(
    recomendacion_id: int,
    data: RecomendacionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "ejecutar"))],
):
    try:
        return await RecomendacionService.actualizar(
            db, recomendacion_id, data.model_dump(exclude_unset=True)
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail) from exc


@router.delete("/{recomendacion_id}", response_model=RecomendacionResponse)
async def eliminar_recomendacion(
    recomendacion_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "ejecutar"))],
):
    try:
        return await RecomendacionService.eliminar(db, recomendacion_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail) from exc
