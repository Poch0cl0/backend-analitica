"""S-4 clinical recommendations endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import verificar_permiso
from app.models.usuario import Usuario
from app.schemas.s4 import S4Response
from app.schemas.s3 import PacienteS3Input
from app.services.recomendacion_service import RecomendacionService

router = APIRouter(prefix="/api/s4", tags=["s4-recomendaciones"])


@router.post("/predict", response_model=S4Response)
async def predecir_s4_endpoint(
    datos: PacienteS3Input,
    _: Annotated[Usuario, Depends(verificar_permiso("recomendacion", "ejecutar"))],
) -> S4Response:
    try:
        resultado = RecomendacionService.ejecutar_modelo(datos.model_dump())
        return S4Response(**resultado)
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
