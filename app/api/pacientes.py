"""Paciente CRUD endpoints."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.paciente import (
    PacienteCreate,
    PacienteListResponse,
    PacientePerfilResponse,
    PacienteResponse,
    PacienteUpdate,
)
from app.services.paciente_service import PacienteService

router = APIRouter(prefix="/api/pacientes", tags=["pacientes"])


@router.get("/", response_model=PacienteListResponse)
async def listar_pacientes(
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
    q: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    medico_id: Optional[int] = Query(None),
    mes_registro: Optional[int] = Query(None, ge=1, le=12),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    # El médico solo puede ver sus propios pacientes asignados
    effective_medico_id = medico_id
    if usuario.rol.nombre == "medico":
        effective_medico_id = usuario.id

    return await PacienteService.listar(
        db, q=q, estado=estado, medico_id=effective_medico_id, mes_registro=mes_registro, page=page, limit=limit
    )


@router.get("/export")
async def exportar_pacientes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
):
    import csv
    import io

    data = await PacienteService.listar(db, page=1, limit=10000)
    rows = data["items"]
    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["id", "dni", "nombre", "apellidos", "email", "activo"])
        writer.writeheader()
        for p in rows:
            writer.writerow({
                "id": p.id, "dni": p.dni, "nombre": p.nombre,
                "apellidos": p.apellidos, "email": p.email, "activo": p.activo,
            })
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="pacientes.csv"'},
        )
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=503, detail="openpyxl no instalado") from None
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["id", "dni", "nombre", "apellidos", "email", "activo"])
    for p in rows:
        ws.append([p.id, p.dni, p.nombre, p.apellidos, p.email, p.activo])
    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="pacientes.xlsx"'},
    )


@router.post("/", response_model=PacienteResponse, status_code=201)
async def crear_paciente(
    data: PacienteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "crear"))],
):
    return await PacienteService.crear(db, data)


@router.get("/{paciente_id}/perfil", response_model=PacientePerfilResponse)
async def obtener_perfil_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    try:
        return await PacienteService.obtener_perfil(db, paciente_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc


@router.get("/{paciente_id}", response_model=PacienteResponse)
async def obtener_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    try:
        return await PacienteService.obtener(db, paciente_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc


@router.put("/{paciente_id}", response_model=PacienteResponse)
async def actualizar_paciente(
    paciente_id: int,
    data: PacienteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "actualizar"))],
):
    try:
        return await PacienteService.actualizar(db, paciente_id, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc


@router.delete("/{paciente_id}", response_model=PacienteResponse)
async def desactivar_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "eliminar"))],
):
    try:
        return await PacienteService.desactivar(db, paciente_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
