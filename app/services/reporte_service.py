"""Report generation service."""

import io
from datetime import datetime

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.paciente import Paciente


class ReporteService:
    @staticmethod
    async def _obtener_paciente_completo(db: AsyncSession, paciente_id: int) -> Paciente:
        result = await db.execute(
            select(Paciente)
            .options(
                selectinload(Paciente.datos_clinicos),
                selectinload(Paciente.predicciones),
                selectinload(Paciente.triages),
            )
            .where(Paciente.id == paciente_id)
        )
        paciente = result.scalar_one_or_none()
        if paciente is None:
            raise NotFoundError("Paciente no encontrado")
        return paciente

    @staticmethod
    async def generar_excel(db: AsyncSession, paciente_id: int) -> bytes:
        paciente = await ReporteService._obtener_paciente_completo(db, paciente_id)
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Paciente"
        ws.append(["Campo", "Valor"])
        ws.append(["DNI", paciente.dni])
        ws.append(["Nombre", f"{paciente.nombre} {paciente.apellidos}"])
        ws.append(["Teléfono", paciente.telefono_principal or ""])
        ws.append(["Email", paciente.email or ""])

        if paciente.datos_clinicos:
            dc = paciente.datos_clinicos
            ws.append(["Edad gestacional", dc.edad_gestacional_semanas])
            ws.append(["BMI", float(dc.bmi) if dc.bmi else ""])
            ws.append(["Longitud cervical (mm)", float(dc.longitud_cervical_mm) if dc.longitud_cervical_mm else ""])

        if paciente.predicciones:
            ultima = sorted(paciente.predicciones, key=lambda p: p.fecha_prediccion)[-1]
            ws.append(["Prob. consenso", float(ultima.prob_consenso) if ultima.prob_consenso else ""])
            ws.append(["Semanas estimadas", ultima.semanas_estimadas_consenso])

        if paciente.triages:
            ultimo = sorted(paciente.triages, key=lambda t: t.fecha_triage)[-1]
            ws.append(["Nivel urgencia", ultimo.nivel_urgencia])

        ws.append(["Generado", datetime.now().isoformat()])
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    @staticmethod
    async def generar_pdf(db: AsyncSession, paciente_id: int) -> bytes:
        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise BadRequestError(
                "WeasyPrint no está disponible en este entorno"
            ) from exc

        paciente = await ReporteService._obtener_paciente_completo(db, paciente_id)
        html = f"""
        <html><body>
        <h1>Reporte ObstetriCare</h1>
        <p><strong>Paciente:</strong> {paciente.nombre} {paciente.apellidos}</p>
        <p><strong>DNI:</strong> {paciente.dni}</p>
        <p><strong>Generado:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </body></html>
        """
        return HTML(string=html).write_pdf()

    @staticmethod
    async def exportar(db: AsyncSession, paciente_id: int, formato: str) -> tuple[bytes, str, str]:
        if formato == "xlsx":
            content = await ReporteService.generar_excel(db, paciente_id)
            return content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "reporte.xlsx"
        if formato == "pdf":
            content = await ReporteService.generar_pdf(db, paciente_id)
            return content, "application/pdf", "reporte.pdf"
        raise BadRequestError("Formato no soportado. Use pdf o xlsx")
