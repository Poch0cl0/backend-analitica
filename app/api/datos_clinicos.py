"""Datos clínicos endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.paciente import DatosClinicosCreate, DatosClinicosResponse, DatosClinicosUpdate
from app.services.datos_clinicos_service import DatosClinicosService

router = APIRouter(prefix="/api/datos-clinicos", tags=["datos-clinicos"])


@router.get("/{paciente_id}", response_model=DatosClinicosResponse)
async def obtener_datos_clinicos(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("datos_clinicos", "leer"))],
):
    return await DatosClinicosService.obtener(db, paciente_id)


@router.post("/{paciente_id}", response_model=DatosClinicosResponse, status_code=201)
async def crear_datos_clinicos(
    paciente_id: int,
    data: DatosClinicosCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("datos_clinicos", "crear"))],
):
    return await DatosClinicosService.crear(db, paciente_id, data)


@router.put("/{paciente_id}", response_model=DatosClinicosResponse)
async def actualizar_datos_clinicos(
    paciente_id: int,
    data: DatosClinicosUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("datos_clinicos", "actualizar"))],
):
    return await DatosClinicosService.actualizar(db, paciente_id, data)
