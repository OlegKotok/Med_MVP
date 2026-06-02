import logging
import smtplib
from email.message import EmailMessage
from app.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, body: str) -> None:
    """Send an email or log it to console in demo mode (SMTP_HOST not set)."""
    if not settings.SMTP_HOST:
        logger.warning("📧 [DEMO] To: %s | Subject: %s | Body: %s", to, subject, body)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg.set_content(body)

    try:
        if settings.SMTP_USE_SSL:
            # Implicit TLS — used by ukr.net port 465, Gmail port 465, etc.
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            # STARTTLS — used by port 587
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(msg)
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", to, exc)
        raise


def send_verification_email(to: str, code: str) -> None:
    _send(to, "Verify your email",
          f"Your verification code is: {code}\n\nValid for 15 minutes.")


def send_password_reset_email(to: str, code: str) -> None:
    _send(to, "Password reset code",
          f"Your password reset code is: {code}\n\nValid for 15 minutes.")


def send_appointment_notification(
    doctor_email: str, client_name: str, client_email: str, scheduled_at: str, notes: str
) -> None:
    body = (
        f"New appointment booked.\n\n"
        f"Client:       {client_name} <{client_email}>\n"
        f"Scheduled at: {scheduled_at}\n"
    )
    if notes:
        body += f"Notes:        {notes}\n"
    _send(doctor_email, "New appointment booked", body)
