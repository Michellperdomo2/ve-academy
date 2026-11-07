"""Envío de correos. Solo funciona si SMTP está configurado; nunca simula envíos."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("ve_academy.email")


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.smtp_configured

    def send(self, to: str, subject: str, body: str) -> bool:
        if not self.enabled:
            logger.warning("SMTP no configurado: no se envió el correo '%s'.", subject)
            return False
        msg = EmailMessage()
        msg["From"] = self.settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT, timeout=10) as smtp:
                if self.settings.SMTP_USE_TLS:
                    smtp.starttls()
                if self.settings.SMTP_USER and self.settings.SMTP_PASSWORD:
                    smtp.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                smtp.send_message(msg)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception("No fue posible enviar el correo a %s", to)
            return False

    def send_password_reset(self, to: str, name: str, token: str) -> bool:
        link = f"{self.settings.FRONTEND_URL.rstrip('/')}/restablecer?token={token}"
        body = (
            f"Hola {name}:\n\n"
            "Recibimos una solicitud para restablecer tu contraseña en V&E Academy.\n"
            f"Abre este enlace (válido por {self.settings.PASSWORD_RESET_EXPIRE_MINUTES} minutos):\n\n"
            f"{link}\n\nSi no fuiste tú, ignora este mensaje."
        )
        return self.send(to, "V&E Academy - Restablecer contraseña", body)
