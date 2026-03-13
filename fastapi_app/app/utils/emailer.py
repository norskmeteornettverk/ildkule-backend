import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_mail(
    recipient: str,
    subject: str,
    html_body: str,
    alt_body: Optional[str] = None,
) -> None:
    """Send an e-mail using SMTP credentials defined in the settings."""

    if not all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.smtp_sender,
        ]
    ):
        logger.warning("SMTP settings missing, skipping outbound e-mail")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = recipient
    msg.set_content(alt_body or html_body, subtype="plain")
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(msg)
    except Exception:
        logger.exception("Failed to send e-mail via SMTP")
        raise

