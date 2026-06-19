"""Paciente CRUD endpoints."""

from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.paciente import PacienteCreate, PacienteResponse, PacienteUpdate
from app.services.paciente_service import PacienteService

router = APIRouter(prefix="/api/pacientes", tags=["pacientes"])


@router.get("/", response_model=List[PacienteResponse])
async def listar_pacientes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    return await PacienteService.listar(db)


@router.post("/", response_model=PacienteResponse, status_code=201)
async def crear_paciente(
    data: PacienteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "crear"))],
):
    return await PacienteService.crear(db, data)


@router.get("/{paciente_id}", response_model=PacienteResponse)
async def obtener_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    return await PacienteService.obtener(db, paciente_id)


@router.put("/{paciente_id}", response_model=PacienteResponse)
async def actualizar_paciente(
    paciente_id: int,
    data: PacienteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "actualizar"))],
):
    return await PacienteService.actualizar(db, paciente_id, data)


@router.delete("/{paciente_id}", response_model=PacienteResponse)
async def desactivar_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "eliminar"))],
):
    return await PacienteService.desactivar(db, paciente_id)
