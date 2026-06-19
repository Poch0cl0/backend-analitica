"""Predicción endpoints — S-2 por paciente."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import verificar_permiso
from app.ml_models.prediccion.predecir_s2 import AlgoritmoS2
from app.models.usuario import Usuario
from app.schemas.prediccion import PrediccionPorPacienteResponse, PrediccionResponse
from app.schemas.s2 import PacienteS2Input, S2Response
from app.services.prediccion_service import PrediccionService

router = APIRouter(prefix="/api/prediccion", tags=["prediccion"])

_ALGORITMOS_DESC = (
    "Algoritmo a usar: "
    "'mejor' (CatBoost, por defecto), "
    "'catboost' (archivo .cbm nativo), "
    "'logistic' (Regresión Logística), "
    "'random_forest' (Random Forest), "
    "'svm' (SVM LinearSVC)"
)


@router.post(
    "/ejecutar/{paciente_id}",
    response_model=PrediccionPorPacienteResponse,
    summary="Predicción S-2 automática con datos clínicos del paciente",
)
async def ejecutar_prediccion_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
    algoritmo: AlgoritmoS2 = Query(default="mejor", description=_ALGORITMOS_DESC),
):
    """
    Ejecuta la predicción S-2 usando los datos clínicos ya registrados del paciente.
    No requiere ingresar campos manualmente. Elige el algoritmo con el parámetro
    `algoritmo` en la query string.
    """
    try:
        return await PrediccionService.ejecutar_para_paciente(
            db, paciente_id, algoritmo=algoritmo, medico=usuario
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
            detail=f"Error al ejecutar predicción: {exc}",
        ) from exc


@router.post(
    "/manual",
    response_model=S2Response,
    summary="Predicción S-2 con campos ingresados manualmente",
)
async def prediccion_manual(
    datos: PacienteS2Input,
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
    algoritmo: AlgoritmoS2 = Query(default="mejor", description=_ALGORITMOS_DESC),
) -> S2Response:
    """Ejecuta S-2 con los 9 campos ingresados directamente. Elige el algoritmo con `algoritmo`."""
    try:
        resultado = PrediccionService.ejecutar_modelo(datos.model_dump(), algoritmo=algoritmo)
        return S2Response(**resultado)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/algoritmos",
    summary="Listar algoritmos disponibles para S-2",
)
async def listar_algoritmos(
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    """Retorna los algoritmos disponibles y cuáles están instalados."""
    from pathlib import Path
    from app.core.config import settings

    dir_modelos = Path(settings.ML_MODELS_PATH)
    archivos = {
        "catboost":      ("prematuro_catboost.cbm",     "semanas_catboost.cbm"),
        "mejor":         ("prematuro_mejor_modelo.pkl",  "semanas_mejor_modelo.pkl"),
        "logistic":      ("prematuro_logistic.pkl",      "semanas_lineal.pkl"),
        "random_forest": ("prematuro_random_forest.pkl", "semanas_random_forest.pkl"),
        "svm":           ("prematuro_svm.pkl",           "semanas_svm.pkl"),
    }
    nombres = {
        "catboost":      "CatBoost (formato nativo .cbm)",
        "mejor":         "CatBoost - Mejor modelo (.pkl)",
        "logistic":      "Regresión Logística",
        "random_forest": "Random Forest",
        "svm":           "SVM (LinearSVC)",
    }
    return [
        {
            "algoritmo":     alg,
            "nombre":        nombres[alg],
            "disponible":    (dir_modelos / pre).exists() and (dir_modelos / sem).exists(),
            "archivo_prematuro": pre,
            "archivo_semanas":   sem,
        }
        for alg, (pre, sem) in archivos.items()
    ]


@router.get(
    "/historial/{paciente_id}",
    response_model=List[PrediccionResponse],
    summary="Historial de predicciones de un paciente",
)
async def historial_predicciones(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    return await PrediccionService.listar_por_paciente(db, paciente_id)
