"""Gmail SMTP email sender."""

import smtplib
import ssl
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_TIMEOUT = 15


def send_email(sender, app_password, recipient, subject, body):
    """Send one plain-text email through Gmail's SSL-protected SMTP service."""
    app_password = "".join(app_password.split())
    try:
        email = EmailMessage()
        email["From"] = sender
        email["To"] = recipient
        email["Subject"] = subject or "(no subject)"
        email.set_content(body)
        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=SMTP_TIMEOUT,
            context=ssl.create_default_context(),
        ) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(email)
    except (smtplib.SMTPException, OSError, ValueError) as error:
        return False, "Failed via Gmail SMTP", str(error)
    return True, "Accepted by Gmail SMTP", ""
