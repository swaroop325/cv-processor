import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str) -> bool:
        """Send email to candidate"""
        try:
            if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                print(f"Email would be sent to {to_email}: {subject}")
                return True  # Return True in dev mode without SMTP configured

            msg = MIMEMultipart()
            msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

