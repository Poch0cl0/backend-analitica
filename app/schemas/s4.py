"""Schemas S-4 — recomendaciones clínicas."""

from typing import Literal

from pydantic import BaseModel, Field

from app.ml_models.recomendaciones.config import RECOMENDACIONES
from app.schemas.s3 import PacienteS3Input

RecomendacionSlug = Literal[
    "control_prenatal_rutinario",
    "seguimiento_estrecho_lc",
    "progesterona_vaginal",
    "tratar_infeccion",
    "vigilancia_hta_multiple",
    "derivacion_alto_riesgo",
]


class PacienteS4Input(PacienteS3Input):
    """10 campos clínicos para inferencia S-4 (modo clinico=True)."""


class EntradasS4Input(BaseModel):
    """9 entradas precomputadas para inferencia S-4 (modo clinico=False)."""

    prob_prematuro: float = Field(..., ge=0, le=1)
    nivel_urgencia: Literal["VERDE", "AMARILLO", "NARANJA", "ROJO"]
    parto_previo: Literal[0, 1]
    cl_sim_mm: float = Field(..., gt=0)
    hipertension_gestacional: Literal[0, 1]
    bmi: float = Field(..., gt=0)
    infeccion_activa: Literal[0, 1]
    num_condiciones_cronicas: int = Field(..., ge=0)
    embarazo_multiple: Literal[0, 1]


class ImportanciaVariableRF(BaseModel):
    variable: str
    importancia: float


class EntradasS4Response(BaseModel):
    prob_prematuro: float
    nivel_urgencia: str
    parto_previo: int
    cl_sim_mm: float
    hipertension_gestacional: int
    bmi: float
    infeccion_activa: int
    num_condiciones_cronicas: int
    embarazo_multiple: int


class S4Response(BaseModel):
    recomendacion_if_then: RecomendacionSlug
    recomendacion_cart: RecomendacionSlug
    recomendacion_random_forest: RecomendacionSlug
    importancia_variables_rf: list[ImportanciaVariableRF]
    entradas_s4: EntradasS4Response
    recomendaciones_posibles: list[str] = Field(default_factory=lambda: list(RECOMENDACIONES))
