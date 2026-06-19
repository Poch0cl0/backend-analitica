"""Schemas de paciente."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PacienteBase(BaseModel):
    dni: str = Field(..., min_length=6, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    fecha_nacimiento: date
    telefono_principal: Optional[str] = None
    email: Optional[str] = None
    medico_asignado_id: Optional[int] = None


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    telefono_principal: Optional[str] = None
    email: Optional[str] = None
    medico_asignado_id: Optional[int] = None
    activo: Optional[bool] = None


class PacienteResponse(PacienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime


class PacienteListResponse(BaseModel):
    items: list[PacienteResponse]
    total: int
    page: int
    pages: int


class PacientePerfilResponse(BaseModel):
    id: int
    dni: str
    nombre: str
    apellidos: str
    telefono_principal: Optional[str] = None
    email: Optional[str] = None
    edad_madre: Optional[int] = None
    edad_gestacional_semanas: Optional[int] = None
    longitud_cervical_mm: Optional[Decimal] = None
    embarazo_multiple: Optional[bool] = None
    parto_prematuro_previo: Optional[bool] = None
    hipertension_gestacional: Optional[bool] = None
    bmi: Optional[Decimal] = None
    num_condiciones_cronicas: Optional[int] = None
    infeccion_activa: Optional[bool] = None
    prob_consenso: Optional[Decimal] = None
    nivel_riesgo: Optional[str] = None
    semanas_estimadas_consenso: Optional[int] = None
    nivel_urgencia: Optional[str] = None
    medico_nombre: Optional[str] = None
    fecha_ultima_prediccion: Optional[datetime] = None
    fecha_ultimo_triage: Optional[datetime] = None


class DatosClinicosBase(BaseModel):
    edad_gestacional_semanas: Optional[int] = Field(None, ge=20, le=45)
    longitud_cervical_mm: Optional[Decimal] = None
    embarazo_multiple: bool = False
    parto_prematuro_previo: bool = False
    hipertension_gestacional: bool = False
    bmi: Optional[Decimal] = None
    bmi_categoria: Optional[str] = None
    num_condiciones_cronicas: int = 0
    infeccion_activa: bool = False
    diabetes_pregestacional: bool = False
    diabetes_gestacional: bool = False
    hipertension_cronica: bool = False
    eclampsia: bool = False
    hepatitis_b: bool = False
    hepatitis_c: bool = False
    sifilis: bool = False
    clamidia: bool = False
    gonorrea: bool = False
    cesareas_previas: bool = False
    num_cesareas: int = 0
    num_partos_previos_vivos: int = 0
    alerta_activa: bool = False
    notas_medicas: Optional[str] = None


class DatosClinicosCreate(DatosClinicosBase):
    pass


class DatosClinicosUpdate(DatosClinicosBase):
    pass


class DatosClinicosResponse(DatosClinicosBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    created_at: datetime
    updated_at: datetime
