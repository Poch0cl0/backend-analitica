"""Dashboard service."""

from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cita import Cita
from app.models.paciente import Paciente


class DashboardService:
    @staticmethod
    async def resumen(db: AsyncSession) -> dict:
        hoy = date.today()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)

        total_pacientes = (
            await db.execute(select(func.count()).select_from(Paciente).where(Paciente.activo.is_(True)))
        ).scalar() or 0

        inicio_hoy = datetime.combine(hoy, datetime.min.time())
        fin_hoy = datetime.combine(hoy, datetime.max.time())

        citas_hoy = (
            await db.execute(
                select(func.count()).select_from(Cita).where(
                    Cita.fecha_hora >= inicio_hoy,
                    Cita.fecha_hora <= fin_hoy,
                    Cita.estado != "cancelada",
                )
            )
        ).scalar() or 0

        citas_pendientes = (
            await db.execute(
                select(func.count()).select_from(Cita).where(
                    Cita.fecha_hora >= inicio_hoy,
                    Cita.fecha_hora <= fin_hoy,
                    Cita.estado == "programada",
                )
            )
        ).scalar() or 0

        citas_pendientes_activas = (
            await db.execute(
                select(func.count()).select_from(Cita).where(
                    Cita.estado.in_(["programada", "en_atencion"]),
                )
            )
        ).scalar() or 0

        inicio_sem = datetime.combine(inicio_semana, datetime.min.time())
        fin_sem = datetime.combine(fin_semana, datetime.max.time())
        citas_semana = (
            await db.execute(
                select(func.count()).select_from(Cita).where(
                    Cita.fecha_hora >= inicio_sem,
                    Cita.fecha_hora <= fin_sem,
                    Cita.estado != "cancelada",
                )
            )
        ).scalar() or 0

        pacientes_con_cita = (
            await db.execute(
                select(func.count(func.distinct(Cita.paciente_id))).where(
                    Cita.fecha_hora >= inicio_sem,
                    Cita.fecha_hora <= fin_sem,
                    Cita.estado != "cancelada",
                )
            )
        ).scalar() or 0
        pacientes_sin_cita = max(0, total_pacientes - pacientes_con_cita)

        return {
            "total_pacientes": total_pacientes,
            "citas_hoy": citas_hoy,
            "citas_pendientes_confirmacion": citas_pendientes,
            "citas_pendientes_activas": citas_pendientes_activas,
            "citas_semana": citas_semana,
            "pacientes_sin_cita": pacientes_sin_cita,
        }
