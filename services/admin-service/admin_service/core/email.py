"""
Email sending for Admin Service (password reset, etc.)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from admin_service.config.settings import settings


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    user_name: str,
) -> bool:
    """
    Send password reset email.
    Uses SMTP (supports MailHog for local dev).
    """
    try:
        reset_url = f"{settings.password_reset_base_url.rstrip('/')}?token={reset_token}"
        subject = "VokeTag - Redefinir senha"
        html = f"""
        <html>
        <body>
        <p>Olá {user_name},</p>
        <p>Você solicitou a redefinição de senha. Clique no link abaixo:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>O link expira em 1 hora.</p>
        <p>Se você não solicitou isso, ignore este email.</p>
        <p>— Equipe VokeTag</p>
        </body>
        </html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_user and settings.smtp_password:
                try:
                    server.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass  # MailHog etc. may not support TLS
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to_email, msg.as_string())
        return True
    except Exception:
        return False
