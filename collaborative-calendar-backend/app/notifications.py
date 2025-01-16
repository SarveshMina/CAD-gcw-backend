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

# Base HTML Template with Blue and Modern Design
BASE_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{{subject}}</title>
  <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* Base styles */
    body {
      background-color: #f0f4f8;
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
      border-bottom: 1px solid #e0e7ef;
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
      color: #1e40af;
      margin-bottom: 10px;
    }

    .content p {
      font-size: 16px;
      color: #4b5563;
    }

    .button {
      display: inline-block;
      margin: 20px 0;
      padding: 12px 25px;
      background-color: #1e40af;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 25px;
      font-weight: bold;
      transition: background-color 0.3s ease;
    }

    .button:hover {
      background-color: #1e3a8a;
    }

    .footer {
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #e0e7ef;
      font-size: 14px;
      color: #9ca3af;
    }

    .footer a {
      color: #1e40af;
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
      <img src="{{logo_url}}" alt="Calendify Logo" />
    </div>
    <div class="content">
      <h2>Hello {{username}},</h2>
      <p>
        {{message}}
      </p>
      {{additional_content}}
      <a href="{{action_url}}" class="button">{{action_text}}</a>
      <p>
        If you have any questions, feel free to reply to this email or contact our support team by replying this email.
      </p>
    </div>
    <div class="footer">
      <p>© 2025 COMP3207 Calendify Group M.</p>
      <p>
        <a href="https://sarveshmina.github.io/CAD-gwc-frontend/contact">Contact Us</a>
      </p>
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
        "To get started, simply click the link below to visit your dashboard:\n"
        "https://sarveshmina.github.io/CAD-gwc-frontend/\n\n"
        "Happy Planning!\n"
        "Calendify Team"
    )

    # Dynamic content for HTML
    message = (
        "Thank you for signing up for <strong>Calendify</strong>! We're thrilled to have you on board."
    )

    additional_content = """
    <h3>What’s Next?</h3>
    <ul>
      <li>Create personal calendars to organize your events.</li>
      <li>Invite friends or colleagues to group calendars for collaborative scheduling.</li>
      <li>Manage your schedule seamlessly across all your devices.</li>
    </ul>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{username}}", username)\
        .replace("{{message}}", message)\
        .replace("{{additional_content}}", additional_content)\
        .replace("{{action_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/")\
        .replace("{{action_text}}", "Go to Dashboard")

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
    action_text: str = "Visit Dashboard",
    action_url: str = "https://sarveshmina.github.io/CAD-gwc-frontend/",
    ip_address: str = None,
    location: dict = None
):
    """
    Sends a beautifully styled general notification email to a user.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param message: Main message content.
    :param action_text: Text for the call-to-action button.
    :param action_url: URL for the call-to-action button.
    :param ip_address: (Optional) IP address related to the notification.
    :param location: (Optional) Location dictionary related to the notification.
    """
    subject = "Calendify Notification"

    # Plain-text fallback
    body_text = f"Hello {username},\n\n{message}\n\n"

    if ip_address and location:
        body_text += (
            f"Details:\n"
            f"IP Address: {ip_address}\n"
            f"Location: {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}\n\n"
        )

    body_text += (
        "If you have any questions, feel free to reply to this email or contact our support team.\n\n"
        "Best regards,\n"
        "Calendify Team"
    )

    # Construct Google Maps URL if location is available
    if location and location.get('lat') and location.get('lon'):
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={location['lat']},{location['lon']}"
    else:
        google_maps_url = "https://www.google.com/maps"

    # Prepare additional content for HTML
    additional_content = ""
    if ip_address and location:
        additional_content = f"""
        <h3>Details:</h3>
        <ul>
          <li><strong>IP Address:</strong> {ip_address}</li>
          <li><strong>Location:</strong> {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}</li>
        </ul>
        <p>
          You can view this location on the map below:
        </p>
        <a href="{google_maps_url}" class="button">View on Google Maps</a>
        """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{username}}", username)\
        .replace("{{message}}", message)\
        .replace("{{additional_content}}", additional_content)\
        .replace("{{action_url}}", action_url)\
        .replace("{{action_text}}", action_text)

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    if success:
        logger.info("Notification email sent to %s", to_email)
    else:
        logger.error("Failed to send notification email to %s", to_email)

def send_otp_email(to_email: str, username: str, otp: str):
    """
    Sends an OTP email to the user.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param otp: The OTP code.
    """
    subject = "Password Reset OTP"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"Your OTP for password reset is: {otp}\n"
        "This OTP is valid for 10 minutes.\n\n"
        "If you did not request this, please ignore this email.\n\n"
        "Best regards,\n"
        "Calendify Team"
    )

    # Dynamic content for HTML
    message = (
        f"Your OTP for password reset is: <strong>{otp}</strong>. This OTP is valid for <strong>10 minutes</strong>."
    )

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{username}}", username)\
        .replace("{{message}}", message)\
        .replace("{{additional_content}}", "")\
        .replace("{{action_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/")\
        .replace("{{action_text}}", "Reset Password")

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    if success:
        logger.info("OTP email sent to %s", to_email)
    else:
        logger.error("Failed to send OTP email to %s", to_email)

def send_login_notification(to_email: str, username: str, ip_address: str, location: dict):
    """
    Sends a login notification email with IP and location.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param ip_address: IP address from which the login was made.
    :param location: Geolocation data associated with the IP address.
    """
    subject = "New Login to Your Calendify Account"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"You have successfully logged into your Calendify account.\n\n"
        f"Details:\n"
        f"IP Address: {ip_address}\n"
        f"Location: {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}\n\n"
        f"If this was not you, please contact our support immediately."
    )

    # Construct Google Maps URL
    if location.get('lat') and location.get('lon'):
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={location['lat']},{location['lon']}"
    else:
        google_maps_url = "https://www.google.com/maps"

    # Dynamic content for HTML
    message = (
        "You have successfully logged into your Calendify account."
    )

    additional_content = f"""
    <h3>Login Details:</h3>
    <ul>
      <li><strong>IP Address:</strong> {ip_address}</li>
      <li><strong>Location:</strong> {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}</li>
    </ul>
    <p>
      If this was not you, please <a href="https://sarveshmina.github.io/CAD-gwc-frontend/contact">contact our support team</a> immediately.
    </p>
    <p>
      You can view your login location on the map below:
    </p>
    <a href="{google_maps_url}" class="button">View on Google Maps</a>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{username}}", username)\
        .replace("{{message}}", message)\
        .replace("{{additional_content}}", additional_content)\
        .replace("{{action_url}}", google_maps_url)\
        .replace("{{action_text}}", "View on Google Maps")

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    if success:
        logger.info("Login notification email sent to %s", to_email)
    else:
        logger.error("Failed to send login notification email to %s", to_email)

def send_password_reset_notification(to_email: str, username: str, ip_address: str, location: dict):
    """
    Sends a password reset notification email with IP and location.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param ip_address: IP address from which the password reset was made.
    :param location: Geolocation data associated with the IP address.
    """
    subject = "Your Calendify Password Was Changed"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"Your Calendify account password was successfully changed.\n\n"
        f"Details:\n"
        f"IP Address: {ip_address}\n"
        f"Location: {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}\n\n"
        f"If you did not make this change, please contact our support team immediately."
    )

    # Construct Google Maps URL
    if location.get('lat') and location.get('lon'):
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={location['lat']},{location['lon']}"
    else:
        google_maps_url = "https://www.google.com/maps"

    # Dynamic content for HTML
    message = (
        "Your Calendify account password was successfully changed."
    )

    additional_content = f"""
    <h3>Change Details:</h3>
    <ul>
      <li><strong>IP Address:</strong> {ip_address}</li>
      <li><strong>Location:</strong> {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}</li>
    </ul>
    <p>
      If you did not make this change, please <a href="https://sarveshmina.github.io/CAD-gwc-frontend/contact">contact our support team</a> immediately.
    </p>
    <p>
      You can view where this change was made on the map below:
    </p>
    <a href="{google_maps_url}" class="button">View on Google Maps</a>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{username}}", username)\
        .replace("{{message}}", message)\
        .replace("{{additional_content}}", additional_content)\
        .replace("{{action_url}}", google_maps_url)\
        .replace("{{action_text}}", "View on Google Maps")

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    if success:
        logger.info("Password reset notification email sent to %s", to_email)
    else:
        logger.error("Failed to send password reset notification email to %s", to_email)
