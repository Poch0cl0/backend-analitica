"""Contactos con pacientes."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.contacto import ContactoCreate, ContactoResponse
from app.services.contacto_service import ContactoService

router = APIRouter(prefix="/api/pacientes", tags=["contactos"])


@router.get("/{paciente_id}/contactos", response_model=List[ContactoResponse])
async def listar_contactos(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    return await ContactoService.listar(db, paciente_id)


@router.post("/{paciente_id}/contactos", response_model=ContactoResponse, status_code=201)
async def crear_contacto(
    paciente_id: int,
    data: ContactoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("pacientes", "actualizar"))],
):
    try:
        return await ContactoService.crear(db, paciente_id, data.tipo, data.nota, medico=usuario)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
