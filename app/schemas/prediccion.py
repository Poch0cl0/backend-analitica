"""Schemas de predicción."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


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
    prob_logistica: Optional[Decimal] = None
    prob_consenso: Optional[Decimal] = None
    semanas_estimadas_logistica: Optional[int] = None
    semanas_estimadas_consenso: Optional[int] = None
    nivel_riesgo: Optional[str] = None
    fecha_prediccion: datetime
