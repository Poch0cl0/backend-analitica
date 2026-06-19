"""S-3 urgency classification endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.s3 import PacienteS3Input, S3Response
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api/s3", tags=["s3-urgencia"])


@router.post("/predict", response_model=S3Response)
async def predecir_s3_endpoint(
    datos: PacienteS3Input,
    _: Annotated[Usuario, Depends(verificar_permiso("triage", "ejecutar"))],
) -> S3Response:
    try:
        resultado = TriageService.ejecutar_modelo(datos.model_dump())
        return S3Response(
            puntaje_s3=resultado["puntaje_s3"],
            urgencia_puntaje=resultado["urgencia_puntaje"],
            urgencia_arbol=resultado["urgencia_arbol"],
            urgencia_ordinal=resultado["urgencia_ordinal"],
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
