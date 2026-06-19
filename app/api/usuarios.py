"""Usuario CRUD endpoints (admin only)."""

from typing import Annotated, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verificar_permiso
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


class MedicoResumen(BaseModel):
    id: int
    nombre: str
    apellidos: str


@router.get("/medicos", response_model=List[MedicoResumen])
async def listar_medicos(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("pacientes", "leer"))],
):
    result = await db.execute(
        select(Usuario)
        .join(Rol, Usuario.rol_id == Rol.id)
        .where(Rol.nombre == "medico", Usuario.activo.is_(True))
        .order_by(Usuario.apellidos, Usuario.nombre)
    )
    return [
        MedicoResumen(id=u.id, nombre=u.nombre, apellidos=u.apellidos)
        for u in result.scalars().all()
    ]


@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("usuarios", "leer"))],
):
    return await UsuarioService.listar(db)


@router.post("/", response_model=UsuarioResponse, status_code=201)
async def crear_usuario(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("usuarios", "crear"))],
):
    return await UsuarioService.crear(db, data)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("usuarios", "actualizar"))],
):
    return await UsuarioService.actualizar(db, usuario_id, data)


@router.delete("/{usuario_id}", response_model=UsuarioResponse)
async def desactivar_usuario(
    usuario_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("usuarios", "eliminar"))],
):
    return await UsuarioService.desactivar(db, usuario_id)
