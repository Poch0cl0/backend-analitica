"""Servicio de envío de correos."""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.exceptions import BadRequestError


class EmailService:
    @staticmethod
    def _smtp_configured() -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_FROM)

    @staticmethod
    def enviar(
        destinatario: str,
        asunto: str,
        cuerpo_html: str,
        adjunto: tuple[bytes, str, str] | None = None,
    ) -> None:
        if not destinatario:
            raise BadRequestError("El destinatario no tiene correo registrado")

        if not EmailService._smtp_configured():
            if settings.DEBUG:
                print(f"[EMAIL DEV] Para: {destinatario}\nAsunto: {asunto}\n{cuerpo_html[:500]}...")
                return
            raise BadRequestError(
                "El servidor de correo no está configurado. "
                "Configure SMTP_HOST y SMTP_FROM en el entorno."
            )

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = destinatario
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        if adjunto:
            content, filename, mime_type = adjunto
            part = MIMEApplication(content, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            if mime_type:
                part.add_header("Content-Type", mime_type)
            msg.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [destinatario], msg.as_string())
