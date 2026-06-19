"""Report generation service."""

import io
from datetime import datetime
from typing import Literal

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.paciente import Paciente
from app.services.email_service import EmailService

TipoReporte = Literal["completo", "prediccion", "triaje"]


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
    def _ultima_prediccion(paciente: Paciente):
        if not paciente.predicciones:
            return None
        return sorted(paciente.predicciones, key=lambda p: p.fecha_prediccion)[-1]

    @staticmethod
    def _ultimo_triage(paciente: Paciente):
        if not paciente.triages:
            return None
        return sorted(paciente.triages, key=lambda t: t.fecha_triage)[-1]

    @staticmethod
    def _generar_html(paciente: Paciente, tipo: TipoReporte) -> str:
        dc = paciente.datos_clinicos
        pred = ReporteService._ultima_prediccion(paciente)
        triage = ReporteService._ultimo_triage(paciente)
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

        titulo = {
            "completo": "Reporte Clínico Integral",
            "prediccion": "Reporte de Predicción de Riesgo",
            "triaje": "Reporte de Triaje y Urgencia",
        }[tipo]

        filas = [
            ("Paciente", f"{paciente.nombre} {paciente.apellidos}"),
            ("DNI", paciente.dni),
            ("Correo", paciente.email or "—"),
            ("Teléfono", paciente.telefono_principal or "—"),
        ]

        if dc and tipo in ("completo", "prediccion", "triaje"):
            filas.extend([
                ("Edad gestacional", f"{dc.edad_gestacional_semanas or '—'} semanas"),
                ("IMC", str(dc.bmi) if dc.bmi else "—"),
                ("Longitud cervical", f"{dc.longitud_cervical_mm or '—'} mm"),
            ])

        if pred and tipo in ("completo", "prediccion"):
            prob = float(pred.prob_consenso) * 100 if pred.prob_consenso else None
            filas.extend([
                ("Probabilidad parto prematuro", f"{prob:.1f}%" if prob is not None else "—"),
                ("Nivel de riesgo", pred.nivel_riesgo or "—"),
                ("Semanas estimadas", str(pred.semanas_estimadas_consenso or "—")),
            ])

        if triage and tipo in ("completo", "triaje"):
            filas.extend([
                ("Nivel de urgencia", (triage.nivel_urgencia or "—").upper()),
                ("Score triaje", str(triage.score_formula_ponderada or "—")),
            ])

        rows_html = "".join(
            f"<tr><td style='padding:8px;border:1px solid #eee;font-weight:600;color:#612853'>{k}</td>"
            f"<td style='padding:8px;border:1px solid #eee'>{v}</td></tr>"
            for k, v in filas
        )

        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;max-width:640px;margin:0 auto">
          <div style="background:#612853;color:white;padding:20px;border-radius:12px 12px 0 0">
            <h1 style="margin:0;font-size:22px">Obstetricare</h1>
            <p style="margin:6px 0 0;opacity:.85">{titulo}</p>
          </div>
          <div style="padding:20px;border:1px solid #eee;border-top:0;border-radius:0 0 12px 12px">
            <p style="color:#666;font-size:13px">Generado el {ahora}</p>
            <table style="width:100%;border-collapse:collapse;margin-top:12px">{rows_html}</table>
            <p style="margin-top:20px;font-size:12px;color:#888">
              Este reporte fue generado automáticamente por el SAT Obstetricare.
              Consulte con su médico obstetra para interpretación clínica.
            </p>
          </div>
        </body></html>
        """

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
    async def generar_pdf(db: AsyncSession, paciente_id: int, tipo: TipoReporte = "completo") -> bytes:
        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise BadRequestError(
                "WeasyPrint no está disponible en este entorno"
            ) from exc

        paciente = await ReporteService._obtener_paciente_completo(db, paciente_id)
        html = ReporteService._generar_html(paciente, tipo)
        return HTML(string=html).write_pdf()

    @staticmethod
    async def enviar_por_correo(
        db: AsyncSession,
        paciente_id: int,
        tipo: TipoReporte = "completo",
    ) -> dict:
        paciente = await ReporteService._obtener_paciente_completo(db, paciente_id)
        if not paciente.email:
            raise BadRequestError(
                "La paciente no tiene correo electrónico registrado. "
                "Actualice sus datos personales antes de enviar el reporte."
            )

        if tipo == "prediccion" and not paciente.predicciones:
            raise BadRequestError("No hay predicción registrada para esta paciente")
        if tipo == "triaje" and not paciente.triages:
            raise BadRequestError("No hay triaje registrado para esta paciente")

        html = ReporteService._generar_html(paciente, tipo)
        asunto_map = {
            "completo": "Reporte clínico — Obstetricare",
            "prediccion": "Reporte de predicción de riesgo — Obstetricare",
            "triaje": "Reporte de triaje y urgencia — Obstetricare",
        }

        adjunto = None
        try:
            pdf_bytes = await ReporteService.generar_pdf(db, paciente_id)
            if pdf_bytes[:4] == b"%PDF":
                adjunto = (pdf_bytes, f"reporte_{paciente.dni}.pdf", "application/pdf")
        except Exception:
            pass

        EmailService.enviar(
            paciente.email,
            asunto_map[tipo],
            html,
            adjunto=adjunto,
        )
        return {
            "enviado": True,
            "email": paciente.email,
            "tipo": tipo,
            "mensaje": f"Reporte enviado a {paciente.email}",
        }

    @staticmethod
    async def exportar(db: AsyncSession, paciente_id: int, formato: str) -> tuple[bytes, str, str]:
        if formato == "xlsx":
            content = await ReporteService.generar_excel(db, paciente_id)
            return content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "reporte.xlsx"
        if formato == "pdf":
            content = await ReporteService.generar_pdf(db, paciente_id)
            return content, "application/pdf", "reporte.pdf"
        raise BadRequestError("Formato no soportado. Use pdf o xlsx")
