"""Schemas de triage."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TriageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    prediccion_id: Optional[int] = None
    nivel_urgencia: str
    score_formula_ponderada: Optional[Decimal] = None
    urgencia_arbol: Optional[str] = None
    urgencia_ordinal: Optional[str] = None
    factores_activos_detalle: Optional[dict[str, Any]] = None
    acciones_urgentes: Optional[dict[str, Any]] = None
    fecha_triage: datetime


class TriageEjecutadoResponse(BaseModel):
    """Respuesta del triaje automático por paciente_id."""
    paciente_id: int
    paciente_nombre: str
    triage_id: int
    prediccion_id: Optional[int] = None
    datos_entrada: dict[str, Any]
    prob_prematuro: Optional[float] = None
    algoritmo_s2: Optional[str] = None
    puntaje_s3: float
    urgencia_puntaje: str
    urgencia_arbol: str
    urgencia_ordinal: str
    nivel_urgencia_consenso: str


class TriagePriorizadoResponse(BaseModel):
    paciente_id: int
    nombre: str
    apellidos: str
    dni: str
    edad_gestacional_semanas: Optional[int] = None
    nivel_urgencia: str
    score_formula_ponderada: Optional[Decimal] = None
    prob_consenso: Optional[Decimal] = None
    semanas_estimadas_consenso: Optional[int] = None
    bmi: Optional[Decimal] = None
    num_condiciones_cronicas: Optional[int] = None
    fecha_triage: datetime
    acciones_urgentes: Optional[list[str]] = None


class TriageResumenResponse(BaseModel):
    rojo: int
    naranja: int
    amarillo: int
    verde: int
