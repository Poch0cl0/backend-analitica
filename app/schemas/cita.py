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


class DisponibilidadSlot(BaseModel):
    hora_inicio: str
    hora_fin: str
    disponible: bool


class DisponibilidadResponse(BaseModel):
    medico_id: int
    fecha: str
    slots: List[DisponibilidadSlot]
