# backend/app/notifications.py

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import datetime  # Added datetime module for proper date formatting

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

# Modernized Base HTML Template with improved aesthetics
BASE_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{subject}}</title>
  <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Base styles */
    body {
      background-color: #f8fafc;
      margin: 0;
      padding: 0;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #334155;
      line-height: 1.6;
    }

    .email-wrapper {
      background-color: #f8fafc;
      padding: 40px 20px;
    }

    .email-container {
      max-width: 600px;
      margin: 0 auto;
      background-color: #ffffff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    }

    .header {
      background-color: #4361ee;
      padding: 30px 40px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }

    .header::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect x="0" y="0" width="100" height="100" fill="%23ffffff" fill-opacity="0.05"/><path d="M0 25 L25 0 L50 25 L75 0 L100 25 L75 50 L100 75 L75 100 L50 75 L25 100 L0 75 L25 50 Z" fill="%23ffffff" fill-opacity="0.05"/></svg>');
      opacity: 0.6;
    }

    .brand-logo {
      display: block;
      width: 160px;
      height: auto;
      margin: 0 auto 15px;
      position: relative;
    }

    .header-title {
      color: #ffffff;
      font-size: 24px;
      margin: 0;
      position: relative;
    }

    .content-wrapper {
      padding: 40px;
    }

    .content {
      position: relative;
    }

    .greeting {
      margin-bottom: 20px;
    }

    .greeting h2 {
      color: #1e293b;
      font-size: 22px;
      font-weight: 600;
      margin: 0;
    }

    .message-body {
      color: #475569;
      font-size: 16px;
      margin-bottom: 30px;
    }

    .message-body strong {
      color: #1e293b;
      font-weight: 600;
    }

    .additional-content-wrapper {
      margin: 25px 0;
    }

    .info-box {
      background-color: #f8fafc;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .info-box h3 {
      color: #1e293b;
      font-size: 18px;
      font-weight: 600;
      margin-top: 0;
      margin-bottom: 15px;
    }

    .info-box ul {
      padding-left: 20px;
      margin: 15px 0;
    }

    .info-box li {
      margin-bottom: 10px;
      color: #475569;
    }

    .info-box p {
      margin: 10px 0;
    }

    .button-container {
      text-align: center;
      margin: 30px 0;
    }

    .button {
      display: inline-block;
      padding: 14px 32px;
      background-color: #4361ee;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 8px;
      font-weight: 600;
      font-size: 16px;
      transition: background-color 0.3s ease;
      box-shadow: 0 4px 6px rgba(67, 97, 238, 0.25);
    }

    .button:hover {
      background-color: #3a56d4;
    }

    .secondary-button {
      display: inline-block;
      padding: 12px 28px;
      background-color: transparent;
      color: #4361ee !important;
      text-decoration: none;
      border: 2px solid #4361ee;
      border-radius: 8px;
      font-weight: 500;
      font-size: 15px;
      margin: 15px 0;
      transition: all 0.3s ease;
    }

    .secondary-button:hover {
      background-color: rgba(67, 97, 238, 0.08);
    }

    .support-message {
      font-size: 15px;
      color: #64748b;
      margin: 30px 0 40px;
      padding-top: 20px;
      border-top: 1px solid #e2e8f0;
    }

    .footer {
      background-color: #f1f5f9;
      padding: 30px;
      text-align: center;
      color: #64748b;
      font-size: 14px;
    }

    .footer-links {
      margin: 15px 0;
    }

    .footer-links a {
      color: #4361ee;
      text-decoration: none;
      margin: 0 8px;
      font-weight: 500;
    }

    .footer-links a:hover {
      text-decoration: underline;
    }

    .social-links {
      margin: 20px 0 15px;
    }

    .social-icon {
      display: inline-block;
      width: 32px;
      height: 32px;
      margin: 0 5px;
      background-color: #e2e8f0;
      border-radius: 50%;
      text-align: center;
      line-height: 32px;
      transition: background-color 0.3s ease;
    }

    .social-icon:hover {
      background-color: #cbd5e1;
    }

    /* Special Components */
    .otp-container {
      background-color: #f8fafc;
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      margin: 25px 0;
    }

    .otp-code {
      font-size: 32px;
      letter-spacing: 5px;
      font-weight: 600;
      color: #1e293b;
      background: #ffffff;
      padding: 15px 20px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      display: inline-block;
      margin: 10px 0 15px;
    }

    .validity-timer {
      font-size: 14px;
      color: #64748b;
      margin-top: 5px;
    }

    .alert-box {
      background-color: #fef2f2;
      border-left: 4px solid #ef4444;
      padding: 15px 20px;
      margin: 25px 0;
      border-radius: 8px;
    }

    .alert-box.warning {
      background-color: #fffbeb;
      border-left-color: #f59e0b;
    }

    .alert-box.success {
      background-color: #f0fdf4;
      border-left-color: #10b981;
    }

    .location-card {
      background-color: #f8fafc;
      border-radius: 12px;
      padding: 20px;
      margin: 25px 0;
      position: relative;
    }

    .location-card-header {
      display: flex;
      align-items: center;
      margin-bottom: 15px;
    }

    .location-icon {
      width: 24px;
      height: 24px;
      margin-right: 10px;
      background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%234361ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>');
      background-repeat: no-repeat;
      background-position: center;
    }

    .location-city {
      font-size: 18px;
      font-weight: 600;
      color: #1e293b;
    }

    .location-details {
      display: flex;
      margin-bottom: 15px;
    }

    .location-detail {
      margin-right: 20px;
      font-size: 14px;
      color: #64748b;
    }

    .location-detail strong {
      color: #475569;
      font-weight: 600;
      display: block;
      margin-bottom: 5px;
    }

    .welcome-message {
      text-align: center;
      margin: 30px 0;
    }

    .welcome-title {
      font-size: 28px;
      color: #1e293b;
      font-weight: 700;
      margin-bottom: 15px;
    }

    .welcome-subtitle {
      color: #64748b;
      font-size: 16px;
      max-width: 400px;
      margin: 0 auto 20px;
    }

    .feature-list {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      margin: 30px 0;
      gap: 20px;
    }

    .feature-item {
      width: calc(50% - 10px);
      background-color: #f8fafc;
      border-radius: 12px;
      padding: 20px;
      text-align: center;
    }

    .feature-icon {
      width: 48px;
      height: 48px;
      margin: 0 auto 15px;
      background-color: rgba(67, 97, 238, 0.1);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .feature-title {
      font-size: 16px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 8px;
    }

    .feature-description {
      font-size: 14px;
      color: #64748b;
    }

    /* Responsive Adjustments */
    @media only screen and (max-width: 600px) {
      .email-wrapper {
        padding: 20px 10px;
      }

      .content-wrapper {
        padding: 25px 20px;
      }

      .header {
        padding: 25px 20px;
      }

      .button, .secondary-button {
        display: block;
        width: 100%;
        text-align: center;
        box-sizing: border-box;
      }

      .feature-item {
        width: 100%;
      }

      .footer {
        padding: 20px;
      }
    }
  </style>
</head>
<body>
  <div class="email-wrapper">
    <div class="email-container">
      <div class="header">
        <img src="{{logo_url}}" alt="Calendify Logo" class="brand-logo" />
        <h1 class="header-title">{{header_title}}</h1>
      </div>
      
      <div class="content-wrapper">
        <div class="content">
          <div class="greeting">
            <h2>Hello {{username}},</h2>
          </div>
          
          <div class="message-body">
            {{message}}
          </div>
          
          <div class="additional-content-wrapper">
            {{additional_content}}
          </div>
          
          <div class="button-container">
            <a href="{{action_url}}" class="button">{{action_text}}</a>
          </div>
          
          <div class="support-message">
            If you have any questions, feel free to <a href="mailto:support@calendify.com">contact our support team</a> or simply reply to this email.
          </div>
        </div>
      </div>
      
      <div class="footer">
        <p>© 2025 COMP3207 Calendify Group M. All rights reserved.</p>
        
        <div class="footer-links">
          <a href="https://sarveshmina.github.io/CAD-gwc-frontend/">Dashboard</a> •
          <a href="https://sarveshmina.github.io/CAD-gwc-frontend/contact">Contact Us</a> •
          <a href="https://sarveshmina.github.io/CAD-gwc-frontend/privacy">Privacy Policy</a>
        </div>
        
        <div class="social-links">
          <a href="#" class="social-icon">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0NzU1NjkiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTggMmgtM2E1IDUgMCAwIDAtNSA1djNINnY0aDR2OGg0di04aDRsMS0yOGgtMVY3YTEgMSAwIDAgMSAxLTFoM1oiLz48L3N2Zz4=" alt="Facebook" />
          </a>
          <a href="#" class="social-icon">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0NzU1NjkiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjMgMyA1IDE3IDFnLTItMkwyMyAzeiIvPjxwYXRoIGQ9Ik0xNSA4IDgxOCAxOXoiLz48L3N2Zz4=" alt="Twitter" />
          </a>
          <a href="#" class="social-icon">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0NzU1NjkiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCBub2xsb3ciIiB4PSIyIiB5PSIyIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHJ4PSI1IiByeT0iNSIvPjxwYXRoIGQ9Ik0xNm4xMWMtLjU2LjMxLTEuMjEuNTMtMS45MS42My0uNTItLjU4LTEuMjctLjk0LTIuMDctLjk0LTEuNTcgMC0yLjg0IDEuMjctMi44NCAyLjgzIDAgMi4yIDAgNC4yLTMuMzEgNi4yMyA4LjMgMCAxMS42NyA0LjYzIDExLjY3LTMuMjRhMS41OCAxLjcxLS4xNyAxLjE0LS44MiAxLjUxeiIvPjwvc3ZnPg==" alt="Instagram" />
          </a>
        </div>
        
        <p class="footer-note">This email was sent to {{email}}.</p>
      </div>
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

    # Create a more welcoming HTML content
    welcome_content = """
    <div class="welcome-message">
      <div class="welcome-title">Welcome to Calendify! 🎉</div>
      <div class="welcome-subtitle">We're thrilled to have you join us. Your journey to better time management starts now.</div>
    </div>
    
    <div class="feature-list">
      <div class="feature-item">
        <div class="feature-icon">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIzIiB5PSI0IiB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHJ4PSIyIiByeT0iMiI+PC9yZWN0PjxsaW5lIHgxPSIxNiIgeTE9IjIiIHgyPSIxNiIgeTI9IjYiPjwvbGluZT48bGluZSB4MT0iOCIgeTE9IjIiIHgyPSI4IiB5Mj0iNiI+PC9saW5lPjxsaW5lIHgxPSIzIiB5MT0iMTAiIHgyPSIyMSIgeTI9IjEwIj48L2xpbmU+PC9zdmc+" alt="Calendar" width="24" height="24"/>
        </div>
        <div class="feature-title">Personal Calendars</div>
        <div class="feature-description">Create and customize calendars for different aspects of your life</div>
      </div>
      
      <div class="feature-item">
        <div class="feature-icon">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTcgMjF2LTJhNCA0IDAgMCAwLTQtNEg1YTQgNCAwIDAgMC00IDR2MiI+PC9wYXRoPjxjaXJjbGUgY3g9IjkiIGN5PSI3IiByPSI0Ij48L2NpcmNsZT48cGF0aCBkPSJNMjMgMjF2LTJhNCA0IDAgMCAwLTMtMy44NyI+PC9wYXRoPjxwYXRoIGQ9Ik0xNiAzLjEzYTQgNCAwIDAgMSAwIDcuNzUiPjwvcGF0aD48L3N2Zz4=" alt="Group" width="24" height="24"/>
        </div>
        <div class="feature-title">Group Calendars</div>
        <div class="feature-description">Collaborate with friends, family, or colleagues</div>
      </div>
      
      <div class="feature-item">
        <div class="feature-icon">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCI+PC9jaXJjbGU+PHBvbHlsaW5lIHBvaW50cz0iMTIgNiAxMiAxMiAxNiAxNCI+PC9wb2x5bGluZT48L3N2Zz4=" alt="Reminder" width="24" height="24"/>
        </div>
        <div class="feature-title">Event Tracking</div>
        <div class="feature-description">Never miss an important date or deadline</div>
      </div>
      
      <div class="feature-item">
        <div class="feature-icon">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIyIiB5PSIzIiB3aWR0aD0iMjAiIGhlaWdodD0iMTQiIHJ4PSIyIiByeT0iMiI+PC9yZWN0PjxsaW5lIHgxPSI4IiB5MT0iMjEiIHgyPSIxNiIgeTI9IjIxIj48L2xpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMTciIHgyPSIxMiIgeTI9IjIxIj48L2xpbmU+PC9zdmc+" alt="Device" width="24" height="24"/>
        </div>
        <div class="feature-title">Multi-device Access</div>
        <div class="feature-description">Access your schedule from any device, anywhere</div>
      </div>
    </div>
    
    <div class="info-box success">
      <h3>Getting Started is Easy:</h3>
      <ul>
        <li>Create your first calendar</li>
        <li>Add important events and reminders</li>
        <li>Invite others to collaborate on group calendars</li>
        <li>Customize your view and notifications</li>
      </ul>
    </div>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Welcome to Calendify!")\
        .replace("{{username}}", username)\
        .replace("{{message}}", "Thank you for signing up for Calendify! We're excited to have you on board.")\
        .replace("{{additional_content}}", welcome_content)\
        .replace("{{action_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/")\
        .replace("{{action_text}}", "Go to Dashboard")\
        .replace("{{email}}", to_email)

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
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
        <div class="location-card">
          <div class="location-card-header">
            <div class="location-icon"></div>
            <div class="location-city">{location.get('city', 'Unknown')}, {location.get('country', '')}</div>
          </div>
          
          <div class="location-details">
            <div class="location-detail">
              <strong>IP Address</strong>
              {ip_address}
            </div>
            <div class="location-detail">
              <strong>Region</strong>
              {location.get('region', 'Unknown')}
            </div>
            <div class="location-detail">
              <strong>Country</strong>
              {location.get('country', 'Unknown')}
            </div>
          </div>
          
          <div class="button-container">
            <a href="{google_maps_url}" class="secondary-button">
              <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTBjMCA3LTkgMTMtOSAxM3MtOS02LTktMTNhOSA5IDAgMCAxIDE4IDB6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+" alt="Location" style="vertical-align: middle; margin-right: 5px;">
              View on Google Maps
            </a>
          </div>
        </div>
        """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Notification")\
        .replace("{{username}}", username)\
        .replace("{{message}}", message)\
        .replace("{{additional_content}}", additional_content)\
        .replace("{{action_url}}", action_url)\
        .replace("{{action_text}}", action_text)\
        .replace("{{email}}", to_email)

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
    Sends an OTP email to the user with a modern, clear design.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param otp: The OTP code.
    """
    subject = "Your Calendify Password Reset Code"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"Your OTP for password reset is: {otp}\n"
        "This OTP is valid for 10 minutes.\n\n"
        "If you did not request this, please ignore this email.\n\n"
        "Best regards,\n"
        "Calendify Team"
    )

    # Create enhanced OTP content
    otp_content = f"""
    <div class="otp-container">
      <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSI0OCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIzIiB5PSIxMSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjExIiByeD0iMiIgcnk9IjIiPjwvcmVjdD48cGF0aCBkPSJNNyAxMVY3YTUgNSAwIDAgMSAxMCAwdjQiPjwvcGF0aD48L3N2Zz4=" alt="Security" style="margin-bottom: 10px;">
      <p style="margin-bottom: 15px;">Use the following code to reset your password:</p>
      <div class="otp-code">{otp}</div>
      <div class="validity-timer">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNCIgaGVpZ2h0PSIxNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NDc0OGIiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCI+PC9jaXJjbGU+PHBvbHlsaW5lIHBvaW50cz0iMTIgNiAxMiAxMiAxNiAxNCI+PC9wb2x5bGluZT48L3N2Zz4=" alt="Timer" style="vertical-align: middle; margin-right: 5px;">
        Valid for <strong>10 minutes</strong> only
      </div>
    </div>
    
    <div class="alert-box warning">
      <p><strong>Did not request this?</strong> If you did not request a password reset, please ignore this email or contact support if you're concerned about your account's security.</p>
    </div>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Password Reset")\
        .replace("{{username}}", username)\
        .replace("{{message}}", "We received a request to reset your password for your Calendify account. Please use the code below to complete the process.")\
        .replace("{{additional_content}}", otp_content)\
        .replace("{{action_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/")\
        .replace("{{action_text}}", "Reset Password")\
        .replace("{{email}}", to_email)

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
    Sends a login notification email with IP and location with an enhanced security-focused design.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param ip_address: IP address from which the login was made.
    :param location: Geolocation data associated with the IP address.
    """
    subject = "New Login to Your Calendify Account"
    
    # Get current time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"You have successfully logged into your Calendify account.\n\n"
        f"Details:\n"
        f"Time: {current_time}\n"
        f"IP Address: {ip_address}\n"
        f"Location: {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}\n\n"
        f"If this was not you, please contact our support immediately."
    )

    # Construct Google Maps URL
    if location.get('lat') and location.get('lon'):
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={location['lat']},{location['lon']}"
    else:
        google_maps_url = "https://www.google.com/maps"

    # Create enhanced login notification content
    login_content = f"""
    <div class="info-box">
      <h3>
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjAgMjFWMmE4LjM4IDguMzggMCAwIDEgNCAyIj48L3BhdGg+PHBhdGggZD0iTTEgMjFWOWE5IDkgMCAwIDEgOC05aDE3djE2Ij48L3BhdGg+PC9zdmc+" alt="Security" style="vertical-align: middle; margin-right: 8px;">
        New Login Detected
      </h3>
      <p>A new login to your account was detected at <strong>{current_time}</strong>.</p>
    </div>
    
    <div class="location-card">
      <div class="location-card-header">
        <div class="location-icon"></div>
        <div class="location-city">{location.get('city', 'Unknown')}, {location.get('country', '')}</div>
      </div>
      
      <div class="location-details">
        <div class="location-detail">
          <strong>IP Address</strong>
          {ip_address}
        </div>
        <div class="location-detail">
          <strong>Region</strong>
          {location.get('region', 'Unknown')}
        </div>
        <div class="location-detail">
          <strong>Date & Time</strong>
          {current_time}
        </div>
      </div>
      
      <div class="button-container">
        <a href="{google_maps_url}" class="secondary-button">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTBjMCA3LTkgMTMtOSAxM3MtOS02LTktMTNhOSA5IDAgMCAxIDE4IDB6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+" alt="Location" style="vertical-align: middle; margin-right: 5px;">
          View on Google Maps
        </a>
      </div>
    </div>
    
    <div class="alert-box warning">
      <p><strong>Wasn't you?</strong> If you did not log in to your account at this time, please <a href="https://sarveshmina.github.io/CAD-gwc-frontend/contact" style="color: #b45309; text-decoration: underline;">contact our support team</a> immediately and change your password.</p>
    </div>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Security Alert")\
        .replace("{{username}}", username)\
        .replace("{{message}}", "We detected a new sign-in to your Calendify account.")\
        .replace("{{additional_content}}", login_content)\
        .replace("{{action_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/settings/security")\
        .replace("{{action_text}}", "Review Account Security")\
        .replace("{{email}}", to_email)

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
    Sends a password reset notification email with IP and location with an enhanced security-focused design.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param ip_address: IP address from which the password reset was made.
    :param location: Geolocation data associated with the IP address.
    """
    subject = "Your Calendify Password Was Changed"
    
    # Get current time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"Your Calendify account password was successfully changed.\n\n"
        f"Details:\n"
        f"Time: {current_time}\n"
        f"IP Address: {ip_address}\n"
        f"Location: {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}\n\n"
        f"If you did not make this change, please contact our support team immediately."
    )

    # Construct Google Maps URL
    if location.get('lat') and location.get('lon'):
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={location['lat']},{location['lon']}"
    else:
        google_maps_url = "https://www.google.com/maps"

    # Create enhanced password reset notification content
    reset_content = f"""
    <div class="info-box">
      <h3>
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIzIiB5PSIxMSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjExIiByeD0iMiIgcnk9IjIiPjwvcmVjdD48cGF0aCBkPSJNNyAxMVY3YTUgNSAwIDAgMSAxMCAwdjQiPjwvcGF0aD48L3N2Zz4=" alt="Security" style="vertical-align: middle; margin-right: 8px;">
        Password Successfully Changed
      </h3>
      <p>Your Calendify account password was successfully changed at <strong>{current_time}</strong>.</p>
    </div>
    
    <div class="location-card">
      <div class="location-card-header">
        <div class="location-icon"></div>
        <div class="location-city">{location.get('city', 'Unknown')}, {location.get('country', '')}</div>
      </div>
      
      <div class="location-details">
        <div class="location-detail">
          <strong>IP Address</strong>
          {ip_address}
        </div>
        <div class="location-detail">
          <strong>Region</strong>
          {location.get('region', 'Unknown')}
        </div>
        <div class="location-detail">
          <strong>Date & Time</strong>
          {current_time}
        </div>
      </div>
      
      <div class="button-container">
        <a href="{google_maps_url}" class="secondary-button">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTBjMCA3LTkgMTMtOSAxM3MtOS02LTktMTNhOSA5IDAgMCAxIDE4IDB6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+" alt="Location" style="vertical-align: middle; margin-right: 5px;">
          View on Google Maps
        </a>
      </div>
    </div>
    
    <div class="alert-box">
      <p><strong>Security Reminder:</strong> If you did not initiate this password change, your account may be compromised. Please <a href="https://sarveshmina.github.io/CAD-gwc-frontend/contact" style="color: #dc2626; text-decoration: underline;">contact our support team</a> immediately.</p>
    </div>
    
    <div class="info-box">
      <h3>Tips for Account Security:</h3>
      <ul>
        <li>Use a strong, unique password for your Calendify account</li>
        <li>Never share your password with anyone</li>
        <li>Always log out when using shared devices</li>
        <li>Regularly check your account for suspicious activity</li>
      </ul>
    </div>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Password Changed")\
        .replace("{{username}}", username)\
        .replace("{{message}}", "This is a confirmation that your Calendify account password has been changed.")\
        .replace("{{additional_content}}", reset_content)\
        .replace("{{action_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/settings/security")\
        .replace("{{action_text}}", "Review Account Settings")\
        .replace("{{email}}", to_email)

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

def send_calendar_invite_email(to_email: str, username: str, inviter_name: str, calendar_name: str, calendar_id: str):
    """
    Sends a calendar invitation email to a user.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param inviter_name: Name of the person who sent the invite.
    :param calendar_name: Name of the calendar being shared.
    :param calendar_id: ID of the calendar being shared.
    """
    subject = f"{inviter_name} has invited you to a Calendify calendar"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"{inviter_name} has invited you to collaborate on the calendar: {calendar_name}\n\n"
        "To accept this invitation and view the calendar, please click the link below:\n"
        f"https://sarveshmina.github.io/CAD-gwc-frontend/calendar/{calendar_id}\n\n"
        "Best regards,\n"
        "Calendify Team"
    )

    # Create enhanced calendar invite content
    invite_content = f"""
    <div class="info-box">
      <h3>
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIzIiB5PSI0IiB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHJ4PSIyIiByeT0iMiI+PC9yZWN0PjxsaW5lIHgxPSIxNiIgeTE9IjIiIHgyPSIxNiIgeTI9IjYiPjwvbGluZT48bGluZSB4MT0iOCIgeTE9IjIiIHgyPSI4IiB5Mj0iNiI+PC9saW5lPjxsaW5lIHgxPSIzIiB5MT0iMTAiIHgyPSIyMSIgeTI9IjEwIj48L2xpbmU+PC9zdmc+" alt="Calendar" style="vertical-align: middle; margin-right: 8px;">
        Calendar Invitation
      </h3>
      <p>You've been invited to collaborate on:</p>
      <div style="background-color: #ffffff; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e2e8f0;">
        <h4 style="margin: 0 0 10px; color: #1e293b; font-size: 18px;">{calendar_name}</h4>
        <p style="margin: 0; color: #64748b; font-size: 14px;">Invited by: <strong>{inviter_name}</strong></p>
      </div>
    </div>
    
    <div class="info-box success">
      <h3>Benefits of Collaboration:</h3>
      <ul>
        <li>Access shared events and schedules</li>
        <li>Coordinate with team members efficiently</li>
        <li>Get notifications for calendar updates</li>
        <li>Stay in sync with the group</li>
      </ul>
    </div>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Calendar Invitation")\
        .replace("{{username}}", username)\
        .replace("{{message}}", f"<strong>{inviter_name}</strong> has invited you to collaborate on a shared calendar.")\
        .replace("{{additional_content}}", invite_content)\
        .replace("{{action_url}}", f"https://sarveshmina.github.io/CAD-gwc-frontend/calendar/{calendar_id}")\
        .replace("{{action_text}}", "Accept & View Calendar")\
        .replace("{{email}}", to_email)

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    if success:
        logger.info("Calendar invitation email sent to %s", to_email)
    else:
        logger.error("Failed to send calendar invitation email to %s", to_email)

def send_event_reminder_email(to_email: str, username: str, event_title: str, event_date: str, event_time: str, calendar_name: str, calendar_id: str, event_id: str):
    """
    Sends an event reminder email to a user.

    :param to_email: Recipient's email address.
    :param username: Recipient's username.
    :param event_title: Title of the event.
    :param event_date: Date of the event (formatted string).
    :param event_time: Time of the event (formatted string).
    :param calendar_name: Name of the calendar containing the event.
    :param calendar_id: ID of the calendar.
    :param event_id: ID of the event.
    """
    subject = f"Reminder: {event_title} - {event_date}"

    # Plain-text fallback
    body_text = (
        f"Hello {username},\n\n"
        f"This is a reminder for your upcoming event:\n"
        f"Event: {event_title}\n"
        f"Date: {event_date}\n"
        f"Time: {event_time}\n"
        f"Calendar: {calendar_name}\n\n"
        "To view more details about this event, click the link below:\n"
        f"https://sarveshmina.github.io/CAD-gwc-frontend/calendar/{calendar_id}/event/{event_id}\n\n"
        "Best regards,\n"
        "Calendify Team"
    )

    # Create enhanced event reminder content
    reminder_content = f"""
    <div style="background-color: #f0f9ff; border-radius: 12px; padding: 25px; margin: 20px 0; border-left: 4px solid #4361ee;">
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSI0OCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTggOGExIDEgMCAwIDMoLTIgMSAxIDAgMCAwLTIgMCI+PC9wYXRoPjxwYXRoIGQ9Ik0zIDBhOSA5IDAgMCAxIDUgMTZoM2wxMjQgMTZhOSA5IDAgMCAxLTktOWMwLS4yLjAtLjkuMS0uOSI+PC9wYXRoPjwvc3ZnPg==" alt="Reminder" width="48" height="48">
      </div>
      
      <h2 style="text-align: center; margin-bottom: 25px; color: #1e293b; font-size: 24px; font-weight: 600;">{event_title}</h2>
      
      <div style="display: flex; justify-content: center; margin-bottom: 20px;">
        <div style="text-align: center; padding: 0 20px;">
          <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Date</div>
          <div style="font-size: 18px; font-weight: 600; color: #1e293b;">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSIzIiB5PSI0IiB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHJ4PSIyIiByeT0iMiI+PC9yZWN0PjxsaW5lIHgxPSIxNiIgeTE9IjIiIHgyPSIxNiIgeTI9IjYiPjwvbGluZT48bGluZSB4MT0iOCIgeTE9IjIiIHgyPSI4IiB5Mj0iNiI+PC9saW5lPjxsaW5lIHgxPSIzIiB5MT0iMTAiIHgyPSIyMSIgeTI9IjEwIj48L2xpbmU+PC9zdmc+" alt="Date" style="vertical-align: middle; margin-right: 5px;">
            {event_date}
          </div>
        </div>
        <div style="text-align: center; padding: 0 20px; border-left: 1px solid #e2e8f0;">
          <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Time</div>
          <div style="font-size: 18px; font-weight: 600; color: #1e293b;">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCI+PC9jaXJjbGU+PHBvbHlsaW5lIHBvaW50cz0iMTIgNiAxMiAxMiAxNiAxNCI+PC9wb2x5bGluZT48L3N2Zz4=" alt="Time" style="vertical-align: middle; margin-right: 5px;">
            {event_time}
          </div>
        </div>
      </div>
      
      <div style="text-align: center; margin-top: 10px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Calendar</div>
        <div style="font-size: 16px; font-weight: 500; color: #1e293b;">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveG0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgOXYxMEg3LjczNWE3LjA0OSA3LjA0OSAwIDAgMS00Ljk5LTIuMDg4IiBvcGFjaXR5PSIwLjUiPjwvcGF0aD48cGF0aCBkPSJNMyA5YTcgNyAwIDAgMSA3LTdoMTF2MS41IiBvcGFjaXR5PSIwLjUiPjwvcGF0aD48cGF0aCBkPSJNMy4wMDQgNWExMyAxMyAwIDAgMCAxIDR2MiIgb3BhY2l0eT0iMC41Ij48L3BhdGg+PC9zdmc+" alt="Calendar" style="vertical-align: middle; margin-right: 5px;">
          {calendar_name}
        </div>
      </div>
    </div>
    
    <div class="button-container" style="text-align: center;">
      <a href="https://sarveshmina.github.io/CAD-gwc-frontend/calendar/{calendar_id}/event/{event_id}" class="secondary-button" style="margin-right: 10px;">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0MzYxZWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMSIgY3k9IjExIiByPSI4Ij48L2NpcmNsZT48bGluZSB4MT0iMjEiIHkxPSIyMSIgeDI9IjE2LjY1IiB5Mj0iMTYuNjUiPjwvbGluZT48L3N2Zz4=" alt="View" style="vertical-align: middle; margin-right: 5px;">
        View Event Details
      </a>
    </div>
    """

    # Populate the base template
    body_html = BASE_HTML_TEMPLATE.replace("{{subject}}", subject)\
        .replace("{{logo_url}}", "https://sarveshmina.github.io/CAD-gwc-frontend/img/logo-dark.d3ac11a8.png")\
        .replace("{{header_title}}", "Event Reminder")\
        .replace("{{username}}", username)\
        .replace("{{message}}", "This is a friendly reminder about your upcoming event.")\
        .replace("{{additional_content}}", reminder_content)\
        .replace("{{action_url}}", f"https://sarveshmina.github.io/CAD-gwc-frontend/calendar/{calendar_id}")\
        .replace("{{action_text}}", "Open Calendar")\
        .replace("{{email}}", to_email)

    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    if success:
        logger.info("Event reminder email sent to %s", to_email)
    else:
        logger.error("Failed to send event reminder email to %s", to_email)