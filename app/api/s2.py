"""S-2 prediction endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import verificar_permiso
from app.ml_models.prediccion.predecir_s2 import AlgoritmoS2
from app.models.usuario import Usuario
from app.schemas.s2 import PacienteS2Input, S2Response
from app.services.prediccion_service import PrediccionService

router = APIRouter(prefix="/api/s2", tags=["s2-prediccion"])

_ALGORITMOS_DESC = (
    "Algoritmo: 'mejor' (CatBoost, default), 'catboost', 'logistic', 'random_forest', 'svm'"
)


@router.post("/predict", response_model=S2Response)
async def predecir_s2_endpoint(
    datos: PacienteS2Input,
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
    algoritmo: AlgoritmoS2 = Query(default="mejor", description=_ALGORITMOS_DESC),
) -> S2Response:
    try:
        resultado = PrediccionService.ejecutar_modelo(datos.model_dump(), algoritmo=algoritmo)
        return S2Response(**resultado)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
