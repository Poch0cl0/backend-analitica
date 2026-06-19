"""Contacto con paciente schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

TipoContacto = Literal["llamada", "email", "whatsapp", "nota"]


class ContactoCreate(BaseModel):
    tipo: TipoContacto
    nota: str = Field(..., min_length=1)


class ContactoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    tipo: str
    nota: str
    medico_id: Optional[int] = None
    created_at: datetime
