"""Schemas de predicción."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ModeloConsensoItem(BaseModel):
    prob_prematuro: float
    semanas_estimadas: float


class ModelosConsenso(BaseModel):
    random_forest: ModeloConsensoItem
    catboost: ModeloConsensoItem
    svm: ModeloConsensoItem


class PrediccionConsensoResponse(BaseModel):
    prediccion_id: int
    prob_consenso: float
    nivel_riesgo: str
    modelos: ModelosConsenso


class PrediccionUltimaResponse(BaseModel):
    prediccion_id: Optional[int] = None
    prob_consenso: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    modelos: Optional[ModelosConsenso] = None
    fecha_prediccion: Optional[datetime] = None


class PrediccionAnalizarResponse(BaseModel):
    datos_clinicos: dict[str, Any]
    prediccion: PrediccionConsensoResponse


class PrediccionPorPacienteResponse(BaseModel):
    paciente_id: int
    paciente_nombre: str
    prediccion_id: int
    datos_entrada: dict[str, Any]
    prob_prematuro: float
    prematuro: int
    semanas_estimadas: float
    algoritmo_usado: Optional[str] = None
    archivo_modelo: Optional[str] = None


class PrediccionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    prob_random_forest: Optional[Decimal] = None
    prob_catboost: Optional[Decimal] = None
    prob_logistica: Optional[Decimal] = None
    prob_consenso: Optional[Decimal] = None
    semanas_estimadas_rf: Optional[int] = None
    semanas_estimadas_cb: Optional[int] = None
    semanas_estimadas_logistica: Optional[int] = None
    semanas_estimadas_consenso: Optional[int] = None
    nivel_riesgo: Optional[str] = None
    fecha_prediccion: datetime


class PrediccionFeedbackCreate(BaseModel):
    voto_correcta: bool
    comentario: Optional[str] = None
    modelo: Optional[str] = None


class PrediccionFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediccion_id: int
    medico_id: int
    modelo: Optional[str] = None
    voto_correcta: bool
    comentario: Optional[str] = None
    created_at: datetime


class FeedbackPorModelo(BaseModel):
    modelo: Optional[str] = None
    total: int
    correctos: int
    incorrectos: int
    precision: float


class FeedbackTemporal(BaseModel):
    fecha: str
    total: int
    correctos: int
    incorrectos: int
    precision: float


class FeedbackEstadisticasResponse(BaseModel):
    total_votos: int
    total_correctos: int
    total_incorrectos: int
    precision_global: float
    por_modelo: list[FeedbackPorModelo]
    temporal: list[FeedbackTemporal]
