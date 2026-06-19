"""Schemas de reportes."""

from pydantic import BaseModel


class ReporteFormato(BaseModel):
    format: str
