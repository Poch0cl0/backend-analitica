"""Datos clínicos endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.paciente import DatosClinicosCreate, DatosClinicosResponse, DatosClinicosUpdate
from app.schemas.prediccion import PrediccionAnalizarResponse
from app.services.datos_clinicos_service import DatosClinicosService
from app.services.prediccion_service import PrediccionService

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


@router.put(
    "/{paciente_id}/analizar",
    response_model=PrediccionAnalizarResponse,
    summary="Actualizar datos clínicos y ejecutar predicción consenso",
)
async def actualizar_y_analizar(
    paciente_id: int,
    data: DatosClinicosUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("datos_clinicos", "actualizar"))],
):
    try:
        datos = await DatosClinicosService.actualizar(db, paciente_id, data)
        prediccion = await PrediccionService.ejecutar_consenso_para_paciente(
            db, paciente_id, medico=usuario
        )
        return PrediccionAnalizarResponse(
            datos_clinicos=DatosClinicosResponse.model_validate(datos).model_dump(),
            prediccion=prediccion,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
