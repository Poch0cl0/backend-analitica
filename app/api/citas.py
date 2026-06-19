"""Citas endpoints."""

from datetime import date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.cita import (
    CitaCreate,
    CitaResponse,
    CitaUpdateEstado,
    DisponibilidadResponse,
    DisponibilidadSlot,
)
from app.services.cita_service import CitaService

router = APIRouter(prefix="/api/citas", tags=["citas"])


@router.get("/", response_model=List[CitaResponse])
async def listar_citas(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("citas", "leer"))],
    fecha: Optional[date] = Query(None),
    medico_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
):
    return await CitaService.listar(db, fecha=fecha, medico_id=medico_id, estado=estado)


@router.post("/", response_model=CitaResponse, status_code=201)
async def agendar_cita(
    data: CitaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("citas", "crear"))],
):
    return await CitaService.crear(db, data)


@router.get("/disponibilidad", response_model=DisponibilidadResponse)
async def obtener_disponibilidad(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("citas", "leer"))],
    medico_id: int = Query(...),
    fecha: date = Query(...),
):
    slots: List[DisponibilidadSlot] = await CitaService.disponibilidad(db, medico_id, fecha)
    return DisponibilidadResponse(medico_id=medico_id, fecha=str(fecha), slots=slots)


@router.put("/{cita_id}/estado", response_model=CitaResponse)
async def cambiar_estado_cita(
    cita_id: int,
    data: CitaUpdateEstado,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("citas", "actualizar"))],
):
    return await CitaService.cambiar_estado(db, cita_id, data.estado)


@router.delete("/{cita_id}", response_model=CitaResponse)
async def cancelar_cita(
    cita_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("citas", "eliminar"))],
):
    return await CitaService.cancelar(db, cita_id)
