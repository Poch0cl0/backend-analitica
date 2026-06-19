"""Triage endpoints."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.s3 import PacienteS3Input
from app.schemas.triage import TriageEjecutadoResponse, TriagePriorizadoResponse, TriageResponse
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api/triage", tags=["triage"])


@router.post(
    "/ejecutar/{paciente_id}/{prediccion_id}",
    response_model=TriageEjecutadoResponse,
    summary="Triaje S-3 usando datos clínicos del paciente y una predicción S-2 existente",
)
async def ejecutar_triage_paciente(
    paciente_id: int,
    prediccion_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("triage", "ejecutar"))],
):
    """
    Ejecuta el triaje S-3 (clasificación de urgencia) para un paciente usando:
    - Sus datos clínicos actuales registrados en la BD.
    - La probabilidad de prematuro de una predicción S-2 ya guardada.

    Pasos:
    1. Carga datos clínicos del paciente.
    2. Recupera la predicción S-2 indicada (debe pertenecer al mismo paciente).
    3. Ejecuta S-3 con 3 métodos: puntaje ponderado, árbol de decisión, logística ordinal.
    4. Determina nivel de urgencia por consenso.
    5. Guarda el triage vinculado a esa predicción.
    """
    try:
        return await TriageService.ejecutar_para_paciente(
            db, paciente_id, prediccion_id=prediccion_id, medico=usuario
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar triaje: {exc}",
        ) from exc


@router.get(
    "/priorizados",
    response_model=List[TriagePriorizadoResponse],
    summary="Lista de pacientes priorizados por urgencia",
)
async def listar_priorizados(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("triage", "leer"))],
):
    try:
        return await TriageService.listar_priorizados(db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error al consultar vista de triage: {exc}",
        ) from exc


@router.post(
    "/recalcular/{paciente_id}",
    response_model=TriageResponse,
    summary="Recalcular triaje con datos ingresados manualmente",
)
async def recalcular_triage(
    paciente_id: int,
    datos: PacienteS3Input,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("triage", "ejecutar"))],
):
    """Permite ingresar los 10 campos manualmente para forzar un recálculo del triaje."""
    try:
        return await TriageService.recalcular(
            db, paciente_id, datos.model_dump(), usuario
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recalcular triaje: {exc}",
        ) from exc
