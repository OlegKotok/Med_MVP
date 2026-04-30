import logging
import smtplib
from email.message import EmailMessage
from app.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to: str, code: str) -> None:
    """Send the 6-digit verification code.

    Uses real SMTP when SMTP_HOST is set; falls back to console logging
    so the demo works without any mail server.
    """
    subject = "Your verification code"
    body = f"Your verification code is: {code}\n\nIt expires when you use it."

    if not settings.SMTP_HOST:
        # Demo mode — print to console so the code is visible during development
        logger.info("📧 [DEMO] Verification email to %s — code: %s", to, code)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)
