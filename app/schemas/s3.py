"""Schemas S-3 — clasificación por urgencia."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.s2 import PacienteS2Input


class PacienteS3Input(PacienteS2Input):
    rf_ghype: Literal["Y", "N"] = Field(..., description="Hipertensión gestacional")


class S3Response(BaseModel):
    puntaje_s3: float
    urgencia_puntaje: str
    urgencia_arbol: str
    urgencia_ordinal: str
