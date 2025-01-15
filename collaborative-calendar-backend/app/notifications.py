import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # e.g. "myusername@gmail.com"
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # e.g. "my-secret-password"
MAIL_FROM = os.getenv("MAIL_FROM")         # e.g. "no-reply@mydomain.com"

def send_email(to_email: str, subject: str, body_text: str) -> bool:
    """
    Sends an email using basic SMTP. Returns True if sent successfully, False otherwise.
    """
    if not to_email:
        logger.warning("No recipient email provided. Skipping send_email.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = to_email

        part = MIMEText(body_text, "plain")
        msg.attach(part)

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())

        logger.info("Email sent successfully to %s", to_email)
        return True
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, str(e))
        return False
