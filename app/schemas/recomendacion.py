"""Schemas de recomendaciones persistidas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.s4 import EntradasS4Response, ImportanciaVariableRF, RecomendacionSlug

PrioridadSlug = Literal["alta", "media", "baja"]
EstadoRecomendacion = Literal["activo", "pendiente", "completado", "cancelada"]


class IntervencionResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    categoria: Optional[str] = None


class RecomendacionListItem(BaseModel):
    id: int
    paciente_nombre: str
    semanas_gestacion: Optional[int] = None
    titulo: str
    tipo: Optional[str] = None
    prioridad: Optional[str] = None
    estado: str
    fecha: date
    medico_nombre: Optional[str] = None


class RecomendacionListResponse(BaseModel):
    items: list[RecomendacionListItem]
    total: int
    page: int
    pages: int


class RecomendacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    prediccion_id: Optional[int] = None
    algoritmo: str
    prioridad: Optional[int] = None
    confianza: Optional[Decimal] = None
    estado: str
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    notas: Optional[str] = None
    fecha_revision: Optional[date] = None
    es_manual: bool = False
    origen: str = "s4_auto"
    fecha_recomendacion: datetime
    intervencion: IntervencionResumen


class RecomendacionManualCreate(BaseModel):
    paciente_id: int
    intervencion_id: int
    titulo: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    notas: Optional[str] = None
    fecha_revision: Optional[date] = None
    prioridad: PrioridadSlug = "media"


class RecomendacionUpdate(BaseModel):
    estado: Optional[EstadoRecomendacion] = None
    prioridad: Optional[PrioridadSlug] = None
    notas: Optional[str] = None
    fecha_revision: Optional[date] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None


class RecomendacionGeminiResult(BaseModel):
    recomendacion_id: int
    recomendacion: RecomendacionSlug
    titulo: str
    descripcion: str
    intervencion: IntervencionResumen


class RecomendacionEjecutadaResponse(BaseModel):
    paciente_id: int
    paciente_nombre: str
    prediccion_id: int
    prob_prematuro: Optional[float] = None
    nivel_urgencia: str = "VERDE"
    recomendacion_gemini: RecomendacionGeminiResult
    # Campos legacy — se mantienen como opcionales para compatibilidad
    datos_entrada: Optional[dict[str, Any]] = None
    algoritmo_s2: Optional[str] = None
    entradas_s4: Optional[EntradasS4Response] = None
    recomendacion_if_then: Optional[RecomendacionSlug] = None
    recomendacion_cart: Optional[RecomendacionSlug] = None
    recomendacion_random_forest: Optional[RecomendacionSlug] = None
    importancia_variables_rf: Optional[list[ImportanciaVariableRF]] = None
    recomendaciones_guardadas: Optional[list[Any]] = None


def prioridad_a_num(slug: str) -> int:
    return {"alta": 1, "media": 2, "baja": 3}.get(slug.lower(), 2)


def prioridad_a_slug(num: int | None) -> str | None:
    if num is None:
        return None
    return {1: "alta", 2: "media", 3: "baja"}.get(num, "media")
