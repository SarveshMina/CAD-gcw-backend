# backend/app/notifications.py

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure logger has at least one handler to avoid "No handler found" warnings
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Email server configurations
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # e.g., "myusername@gmail.com"
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # e.g., "my-secret-password"
MAIL_FROM = os.getenv("MAIL_FROM")         # e.g., "no-reply@mydomain.com"

def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str = None
) -> bool:
    """
    Sends an email using SMTP. Supports both plain-text and HTML content.
    Returns True if sent successfully, False otherwise.

    :param to_email: Recipient's email address.
    :param subject: Subject of the email.
    :param body_text: Plain-text version of the email body.
    :param body_html: (Optional) HTML version of the email body.
    """
    if not to_email:
        logger.warning("No recipient email provided. Skipping send_email.")
        return False

    try:
        # Create a multipart/alternative container.
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = to_email

        # Attach the plain-text part first.
        part_text = MIMEText(body_text, "plain")
        msg.attach(part_text)

        # Attach the HTML part if provided.
        if body_html:
            part_html = MIMEText(body_html, "html")
            msg.attach(part_html)

        # Send the email via SMTP.
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())

        logger.info("Email sent successfully to %s", to_email)
        return True

    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, str(e))
        return False

# Enhanced HTML templates

HTML_TEMPLATE_ENHANCED = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Welcome to Calendify</title>
  <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* Base styles */
    body {
      background-color: #f4f6f8;
      margin: 0;
      padding: 0;
      font-family: 'Roboto', Arial, sans-serif;
      color: #333333;
    }

    .email-container {
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .header {
      text-align: center;
      padding-bottom: 20px;
      border-bottom: 1px solid #eaeaea;
    }

    .header img {
      max-width: 100px;
      height: auto;
    }

    .content {
      padding: 20px 0;
      line-height: 1.6;
    }

    .content h2 {
      color: #0078d4;
      margin-bottom: 10px;
    }

    .content p {
      font-size: 16px;
      color: #555555;
    }

    .button {
      display: inline-block;
      margin: 20px 0;
      padding: 12px 25px;
      background-color: #0078d4;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 25px;
      font-weight: bold;
      transition: background-color 0.3s ease;
    }

    .button:hover {
      background-color: #005fa3;
    }

    .footer {
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eaeaea;
      font-size: 14px;
      color: #999999;
    }

    .footer a {
      color: #0078d4;
      text-decoration: none;
      margin: 0 5px;
    }

    .footer a:hover {
      text-decoration: underline;
    }

    /* Responsive Design */
    @media only screen and (max-width: 600px) {
      .email-container {
        margin: 20px;
        padding: 15px;
      }

      .content h2 {
        font-size: 1.5em;
      }

      .content p {
        font-size: 15px;
      }

      .button {
        padding: 10px 20px;
        font-size: 14px;
      }
    }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <!-- Placeholder for Logo -->
      <img src="https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-light.868008af.webp" alt="Calendify Logo" />
    </div>
    <div class="content">
      <h2>Hello {{username}},</h2>
      <p>
        Thank you for signing up for <strong>Calendify</strong>! We're thrilled to have you on board.
      </p>
      <p>
        To get started, simply click the button below to visit your dashboard:
      </p>
      <a href="https://sarveshmina.github.io/CAD-gwc-frontend/" class="button">Go to Dashboard</a>
      <p>
        If you did not request this account, please ignore this email or contact our support team.
      </p>
      <h3>What’s Next?</h3>
      <ul>
        <li>Create personal calendars to organize your events.</li>
        <li>Invite friends or colleagues to group calendars for collaborative scheduling.</li>
        <li>Manage your schedule seamlessly across all your devices.</li>
      </ul>
      <p>Happy Planning!</p>
    </div>
    <div class="footer">
      <p>© 2025 Group M Calendify Team.</p>
    </div>
  </div>
</body>
</html>
"""

HTML_TEMPLATE_NOTIFICATION = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Calendify Notification</title>
  <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* Base styles */
    body {
      background-color: #f4f6f8;
      margin: 0;
      padding: 0;
      font-family: 'Roboto', Arial, sans-serif;
      color: #333333;
    }

    .email-container {
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .header {
      text-align: center;
      padding-bottom: 20px;
      border-bottom: 1px solid #eaeaea;
    }

    .header img {
      max-width: 100px;
      height: auto;
    }

    .content {
      padding: 20px 0;
      line-height: 1.6;
    }

    .content h2 {
      color: #0078d4;
      margin-bottom: 10px;
    }

    .content p {
      font-size: 16px;
      color: #555555;
    }

    .button {
      display: inline-block;
      margin: 20px 0;
      padding: 12px 25px;
      background-color: #0078d4;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 25px;
      font-weight: bold;
      transition: background-color 0.3s ease;
    }

    .button:hover {
      background-color: #005fa3;
    }

    .footer {
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eaeaea;
      font-size: 14px;
      color: #999999;
    }

    .footer a {
      color: #0078d4;
      text-decoration: none;
      margin: 0 5px;
    }

    .footer a:hover {
      text-decoration: underline;
    }

    /* Responsive Design */
    @media only screen and (max-width: 600px) {
      .email-container {
        margin: 20px;
        padding: 15px;
      }

      .content h2 {
        font-size: 1.5em;
      }

      .content p {
        font-size: 15px;
      }

      .button {
        padding: 10px 20px;
        font-size: 14px;
      }
    }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <!-- Placeholder for Logo -->
      <img src="https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-light.868008af.webp" alt="Calendify Logo" />
    </div>
    <div class="content">
      <h2>Hello {{username}},</h2>
      <p>
        {{message}}
      </p>
        If you have any questions, feel free to reply to this email or contact our support team.
      </p>
    </div>
    <div class="footer">
      <p>© COMP3207 Group M Calendify Team. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

def send_welcome_email(to_email: str, username: str):
    """
    Sends a beautifully styled welcome email to a new user.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    """
    subject = "Welcome to Calendify!"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        "Thank you for signing up for Calendify! "
        "We're excited to have you on board.\n\n"
        "To get started, visit your dashboard at https://sarveshmina.github.io/CAD-gwc-frontend/\n\n"
        "Happy Planning!\n"
        "Calendify Team"
    )

    # Insert dynamic data into the HTML template
    body_html = HTML_TEMPLATE_ENHANCED.replace("{{username}}", username)

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,    # Plain-text fallback
        body_html=body_html     # HTML version
    )

    if success:
        logger.info("Welcome email sent to %s", to_email)
    else:
        logger.error("Failed to send welcome email to %s", to_email)

def send_notification_email(
    to_email: str,
    username: str,
    message: str,
    action_text: str = None,
    action_url: str = "https://sarveshmina.github.io/CAD-gwc-frontend/"
):
    """
    Sends a beautifully styled general notification email to a user.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param message: The main notification message.
    :param action_text: (Optional) The text to display on the action button.
    :param action_url: (Optional) The URL the action button should link to. Defaults to the dashboard.
    """
    subject = "Calendify Notification"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"{message}\n\n"
    )

    # if action_text and action_url:
    #     body_text += (
    #         f"To take action, visit the following link:\n{action_url}\n\n"
    #     )

    body_text += (
        "If you have any questions, feel free to reply to this email or contact our support team.\n\n"
        "Best regards,\n"
        "Calendify Team"
    )

    # Start with the enhanced HTML template
    body_html = HTML_TEMPLATE_NOTIFICATION.replace("{{username}}", username).replace("{{message}}", message)

    # # Handle optional action button using simple string replacement
    # if action_text and action_url:
    #     # Simple string replacement for the action button
    #     action_button_html = f'<a href="{action_url}" class="button">{action_text}</a>'
    #     # Insert the action button after the message paragraph
    #     # Assuming the message is within a <p> tag, insert before closing </p>
    #     body_html = body_html.replace('</p>', f'</p>\n{action_button_html}', 1)
    # else:
    #     # Remove the button section if no action is provided
    #     body_html = body_html.replace('<a href="{{action_url}}" class="button">{{action_text}}</a>', '')

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,    # Plain-text fallback
        body_html=body_html     # HTML version
    )

    if success:
        logger.info("Notification email sent to %s", to_email)
    else:
        logger.error("Failed to send notification email to %s", to_email)



def send_otp_email(to_email: str, username: str, otp: str):
    """
    Sends an OTP email to the user.
    """
    subject = "Password Reset OTP"

    body_text = (
        f"Hello {username},\n\n"
        f"Your OTP for password reset is: {otp}\n"
        "This OTP is valid for 10 minutes.\n\n"
        "If you did not request this, please ignore this email.\n\n"
        "Best regards,\nCalendify Team"
    )

    send_email(to_email, subject, body_text)
