"""Schemas S-2 — predicción prematuro y semanas."""

from typing import Literal

from pydantic import BaseModel, Field


class PacienteS2Input(BaseModel):
    mager: float = Field(..., ge=10, le=60, description="Edad materna")
    rf_ppterm: Literal["Y", "N"] = Field(..., description="Parto prematuro previo")
    dplural: int = Field(..., ge=1, le=5, description="Número de fetos")
    num_condiciones_cronicas: int = Field(..., ge=0, le=10)
    infeccion_activa: Literal[0, 1]
    priorlive: int = Field(..., ge=0)
    bmi: float = Field(..., ge=10, le=60)
    cl_sim_mm: float = Field(..., ge=0)
    combgest: float = Field(..., ge=20, le=45, description="Edad gestacional combinada")


class S2Response(BaseModel):
    prob_prematuro: float
    prematuro: int
    semanas_estimadas: float
    algoritmo_usado: str | None = None
    archivo_modelo: str | None = None
