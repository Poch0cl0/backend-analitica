"""Dashboard schemas."""

from pydantic import BaseModel


class DashboardResumen(BaseModel):
    total_pacientes: int
    citas_hoy: int
    citas_pendientes_confirmacion: int
    citas_semana: int
    pacientes_sin_cita: int
