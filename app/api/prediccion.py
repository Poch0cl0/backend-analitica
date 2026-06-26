"""Predicción endpoints — S-2 por paciente."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import verificar_permiso
from app.ml_models.prediccion.predecir_s2 import AlgoritmoS2
from app.models.usuario import Usuario
from app.schemas.prediccion import (
    FeedbackEstadisticasResponse,
    PrediccionConsensoResponse,
    PrediccionFeedbackCreate,
    PrediccionFeedbackResponse,
    PrediccionPorPacienteResponse,
    PrediccionResponse,
    PrediccionUltimaResponse,
)
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
    "/consenso/{paciente_id}",
    response_model=PrediccionConsensoResponse,
    summary="Predicción consenso: RF + CatBoost + SVM con promedio",
)
async def ejecutar_consenso_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    try:
        return await PrediccionService.ejecutar_consenso_para_paciente(
            db, paciente_id, medico=usuario
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get(
    "/paciente/{paciente_id}/ultima",
    response_model=PrediccionUltimaResponse,
    summary="Última predicción consenso guardada",
)
async def ultima_prediccion_paciente(
    paciente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    resultado = await PrediccionService.obtener_ultima_consenso(db, paciente_id)
    if resultado is None:
        return PrediccionUltimaResponse()
    return PrediccionUltimaResponse(**resultado)


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
    from app.ml_models.paths import resolve_ml_models_dir
    from app.ml_models.prediccion.predecir_s2 import _ARCHIVOS, _NOMBRES_DISPLAY

    dir_modelos = resolve_ml_models_dir()
    return [
        {
            "algoritmo":     alg,
            "nombre":        _NOMBRES_DISPLAY[alg],
            "disponible":    (dir_modelos / pre).exists() and (dir_modelos / sem).exists(),
            "archivo_prematuro": pre,
            "archivo_semanas":   sem,
        }
        for alg, (pre, sem) in _ARCHIVOS.items()
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


@router.get(
    "/{prediccion_id}/feedback",
    response_model=PrediccionFeedbackResponse,
    summary="Obtener feedback de un médico sobre una predicción",
)
async def obtener_feedback(
    prediccion_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
    modelo: str | None = Query(default=None, description="Filtrar por modelo"),
):
    feedback = await PrediccionService.obtener_feedback(db, prediccion_id, modelo=modelo)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback no encontrado")
    return feedback


@router.post(
    "/{prediccion_id}/feedback",
    response_model=PrediccionFeedbackResponse,
    summary="Guardar o actualizar feedback de una predicción",
    status_code=status.HTTP_201_CREATED,
)
async def guardar_feedback(
    prediccion_id: int,
    data: PrediccionFeedbackCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    feedback = await PrediccionService.guardar_feedback(
        db, prediccion_id, usuario.id, data.model_dump()
    )
    return feedback


@router.get(
    "/{prediccion_id}/feedback/todos",
    response_model=List[PrediccionFeedbackResponse],
    summary="Listar todo el feedback de una predicción",
)
async def listar_feedback(
    prediccion_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    return await PrediccionService.listar_feedback(db, prediccion_id)


@router.get(
    "/feedback/estadisticas",
    response_model=FeedbackEstadisticasResponse,
    summary="Estadísticas globales de feedback para gráficos",
)
async def estadisticas_feedback(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Usuario, Depends(verificar_permiso("prediccion", "ejecutar"))],
):
    return await PrediccionService.obtener_estadisticas(db)
