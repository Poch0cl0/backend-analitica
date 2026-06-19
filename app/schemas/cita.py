"""Schemas de citas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CitaCreate(BaseModel):
    paciente_id: int
    medico_id: int
    fecha_hora: datetime
    duracion_minutos: int = Field(default=30, ge=15, le=120)
    motivo: Optional[str] = None
    notas: Optional[str] = None


class CitaUpdateEstado(BaseModel):
    estado: str = Field(..., pattern="^(programada|en_atencion|cumplida|cancelada)$")


class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    medico_id: Optional[int] = None
    estado: Optional[str] = Field(None, pattern="^(programada|en_atencion|cumplida|cancelada)$")
    motivo: Optional[str] = None
    notas: Optional[str] = None
    duracion_minutos: Optional[int] = Field(None, ge=15, le=120)


class CitaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    medico_id: int
    fecha_hora: datetime
    duracion_minutos: int
    estado: str
    motivo: Optional[str] = None
    notas: Optional[str] = None
    created_at: datetime


class CitaResponseEnriquecida(CitaResponse):
    paciente_nombre: Optional[str] = None
    medico_nombre: Optional[str] = None
    semanas_gestacion: Optional[int] = None
    nivel_riesgo: Optional[str] = None


class DisponibilidadSlot(BaseModel):
    hora_inicio: str
    hora_fin: str
    disponible: bool


class DisponibilidadResponse(BaseModel):
    medico_id: int
    fecha: str
    slots: List[DisponibilidadSlot]
