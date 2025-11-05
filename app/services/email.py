import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from datetime import datetime, timezone
from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    async def send_email(
        recipient_email: str,
        subject: str,
        body_text: str
    ) -> Dict[str, Any]:
        """
        Send email to recipient

        Args:
            recipient_email: Primary recipient email address
            subject: Email subject
            body_text: Email body content (plain text)

        Returns:
            Dictionary containing email send status and details
        """
        try:
            sender_email = settings.SMTP_USER
            logger.info(f"Sending email to {recipient_email} with subject: {subject}")

            # Development mode - no SMTP configured
            if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                log_message = f"[DEV MODE] Email would be sent to {recipient_email}: {subject}"
                logger.info(log_message)
                print(log_message)

                return {
                    "status": "success",
                    "message": f"Email sent to {recipient_email} (dev mode)",
                    "recipient": recipient_email,
                    "subject": subject,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender_email, [recipient_email], msg.as_string())

            log_message = f"Email sent to {recipient_email} successfully"
            logger.info(log_message + "!")

            return {
                "status": "success",
                "message": f"Email sent to {recipient_email}",
                "recipient": recipient_email,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "recipient": recipient_email,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

