# user_routes.py

import random
import string
import datetime
import bcrypt
import json
import logging
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
import azure.functions as func
import os
from dotenv import load_dotenv

from app.database import user_container, calendars_container
from app.models import User, Calendar
from app.notifications import send_email, send_welcome_email, send_notification_email

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def register_user(user_data: User):
    logger.info("Received request to register user: %s", user_data.username)

    # Validate username & password
    if not (5 <= len(user_data.username) <= 15):
        return {"error": "Username must be between 5 and 15 characters"}, 400
    if not (8 <= len(user_data.password) <= 15):
        return {"error": "Password must be between 8 and 15 characters"}, 400

    try:
        # Check if username already exists
        existing_user = list(
            user_container.query_items(
                query="SELECT * FROM Users u WHERE u.username = @username",
                parameters=[{"name": "@username", "value": user_data.username}],
                enable_cross_partition_query=True
            )
        )
        if existing_user:
            return {"error": "Username already exists"}, 400

        # Check if email already exists
        existing_email = list(
            user_container.query_items(
                query="SELECT * FROM Users u WHERE u.email = @email",
                parameters=[{"name": "@email", "value": user_data.email}],
                enable_cross_partition_query=True
            )
        )
        if existing_email:
            return {"error": "Email is already registered"}, 400

        # Hash password
        hashed_password = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
        user_data.password = hashed_password.decode("utf-8")

        # Build user document
        user_item = user_data.dict()
        user_item["id"] = user_data.userId  # Ensure 'id' is set for Cosmos DB

        # Create user document in Cosmos DB
        user_container.create_item(body=user_item)

        # Create default/home calendar
        home_cal = Calendar(
            name=f"{user_data.username}'s Home Calendar",
            ownerId=user_data.userId,
            isGroup=False,
            isDefault=True,
            members=[user_data.userId]
        )
        home_cal_dict = home_cal.dict()
        home_cal_dict["id"] = home_cal.calendarId  # Ensure 'id' is set for Cosmos DB
        home_cal_dict["color"] = "blue"

        # Create calendar document in Cosmos DB
        calendars_container.create_item(body=home_cal_dict)

        # Update user with default_calendar_id
        user_data.calendars.append(home_cal.calendarId)
        user_data.default_calendar_id = home_cal.calendarId

        # Upsert updated user document with calendar info
        updated_user_item = user_data.dict()
        updated_user_item["id"] = user_data.userId
        user_container.upsert_item(body=updated_user_item)

        # Send "account created" email
        send_welcome_email(user_data.email, user_data.username)

        return {
            "message": "User registered successfully",
            "userId": user_data.userId,
            "homeCalendarId": home_cal.calendarId
        }, 201

    except CosmosResourceExistsError:
        return {"error": "User already exists"}, 400
    except CosmosHttpResponseError as e:
        logger.exception("Cosmos HTTP error for user '%s': %s", user_data.username, str(e))
        return {"error": f"(BadRequest) {str(e)}"}, 500
    except Exception as e:
        logger.exception("Unexpected error during user registration: %s", str(e))
        return {"error": "An unexpected error occurred during registration."}, 500


def login_user(username: str, password: str):
    logger.info("Received login request for username: %s", username)

    try:
        user_query = list(
            user_container.query_items(
                query="SELECT * FROM Users u WHERE u.username = @username",
                parameters=[{"name": "@username", "value": username}],
                enable_cross_partition_query=True
            )
        )
        if not user_query:
            logger.warning("Login failed: user '%s' not found", username)
            return {"error": "User not found"}, 404

        user_doc = user_query[0]
        if bcrypt.checkpw(password.encode("utf-8"), user_doc["password"].encode("utf-8")):
            logger.info("User '%s' logged in successfully", username)
            return {
                "message": "Login successful",
                "userId": user_doc["userId"],
                "default_calendar_id": user_doc.get("default_calendar_id", "")
            }, 200
        else:
            logger.warning("Invalid credentials for user '%s'", username)
            return {"error": "Invalid credentials"}, 401

    except CosmosHttpResponseError as e:
        logger.exception("Cosmos HTTP error during login for user '%s': %s", username, str(e))
        return {"error": f"(BadRequest) {str(e)}"}, 500
    except Exception as e:
        logger.exception("Unexpected error during login for user '%s': %s", username, str(e))
        return {"error": "An unexpected error occurred during login."}, 500


def update_user_profile(user_id: str, updates: dict):
    """
    Allows updating username, email, or password. Sends an email if successful.
    """
    logger.info("User '%s' requested profile update.", user_id)
    try:
        # 1) Fetch the user doc
        user_query = list(
            user_container.query_items(
                query="SELECT * FROM Users u WHERE u.userId = @userId",
                parameters=[{"name": "@userId", "value": user_id}],
                enable_cross_partition_query=True
            )
        )
        if not user_query:
            return {"error": "User not found"}, 404

        user_doc = user_query[0]

        # 2) Update permitted fields
        updated = False
        valid_fields = ["username", "email", "password"]
        for field in valid_fields:
            if field in updates:
                new_val = updates[field].strip()

                if field == "username":
                    if not (5 <= len(new_val) <= 15):
                        return {"error": "Username must be 5-15 characters"}, 400
                    # Check if the new username already exists
                    existing_user = list(
                        user_container.query_items(
                            query="SELECT * FROM Users u WHERE u.username = @username AND u.userId != @userId",
                            parameters=[
                                {"name": "@username", "value": new_val},
                                {"name": "@userId", "value": user_id}
                            ],
                            enable_cross_partition_query=True
                        )
                    )
                    if existing_user:
                        return {"error": "Username already exists"}, 400
                    user_doc[field] = new_val

                elif field == "email":
                    # Basic check
                    if "@" not in new_val or "." not in new_val:
                        return {"error": "Invalid email address"}, 400
                    # Check if the new email already exists
                    existing_email = list(
                        user_container.query_items(
                            query="SELECT * FROM Users u WHERE u.email = @email AND u.userId != @userId",
                            parameters=[
                                {"name": "@email", "value": new_val},
                                {"name": "@userId", "value": user_id}
                            ],
                            enable_cross_partition_query=True
                        )
                    )
                    if existing_email:
                        return {"error": "Email is already registered"}, 400
                    user_doc[field] = new_val

                elif field == "password":
                    if not (8 <= len(new_val) <= 15):
                        return {"error": "Password must be 8-15 characters"}, 400
                    hashed_password = bcrypt.hashpw(new_val.encode("utf-8"), bcrypt.gensalt())
                    user_doc[field] = hashed_password.decode("utf-8")

                updated = True

        if not updated:
            return {"error": "No valid fields to update"}, 400

        # 3) Upsert the updated user doc
        user_container.upsert_item(body=user_doc)

        # 4) Send "profile updated" email
        subject = "Your Profile Was Updated"
        body_text = (
            f"Hello {user_doc['username']},\n\n"
            "Your profile details have been updated successfully.\n"
            "If you did not make this change, please contact support immediately.\n\n"
            "Best,\nCalendar App"
        )
        send_email(user_doc["email"], subject, body_text)

        return {"message": "User updated successfully"}, 200

    except CosmosHttpResponseError as e:
        logger.exception("Cosmos HTTP error during profile update for user '%s': %s", user_id, str(e))
        return {"error": f"(BadRequest) {str(e)}"}, 500
    except Exception as e:
        logger.exception("Unexpected error during profile update for user '%s': %s", user_id, str(e))
        return {"error": "An unexpected error occurred during profile update."}, 500


def generate_otp(length=6):
    """Generates a random OTP of the given length."""
    return ''.join(random.choices(string.digits, k=length))


def forgot_password_request(req):
    """
    Handles the forgot password request. Generates and sends an OTP to the user's email.
    """
    try:
        req_body = req.get_json()
        email = req_body.get("email")

        if not email:
            return func.HttpResponse(json.dumps({"error": "Email is required"}), status_code=400, mimetype="application/json")

        # Fetch user from DB
        user_query = list(user_container.query_items(
            query="SELECT * FROM Users u WHERE u.email = @email",
            parameters=[{"name": "@email", "value": email}],
            enable_cross_partition_query=True
        ))

        if not user_query:
            return func.HttpResponse(json.dumps({"error": "User not found"}), status_code=404, mimetype="application/json")

        user_doc = user_query[0]
        user_id = user_doc["userId"]

        # Generate OTP
        otp = generate_otp()
        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

        # Store OTP in user's document
        user_doc["reset_otp"] = otp
        user_doc["otp_expiry"] = expiry_time.isoformat()

        user_container.upsert_item(user_doc)

        # Send OTP email
        subject = "Password Reset OTP"
        message = f"Your OTP for password reset is: {otp}. This OTP is valid for 10 minutes."
        send_notification_email(email, user_doc["username"], message)

        return func.HttpResponse(json.dumps({"message": "OTP sent successfully"}), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.exception("Error in forgot_password_request: %s", str(e))
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def reset_password(req):
    """
    Handles password reset after OTP verification.
    """
    try:
        req_body = req.get_json()
        email = req_body.get("email")
        otp = req_body.get("otp")
        new_password = req_body.get("newPassword")

        if not email or not otp or not new_password:
            return func.HttpResponse(json.dumps({"error": "Email, OTP, and new password are required"}), status_code=400, mimetype="application/json")

        # Fetch user from DB
        user_query = list(user_container.query_items(
            query="SELECT * FROM Users u WHERE u.email = @email",
            parameters=[{"name": "@email", "value": email}],
            enable_cross_partition_query=True
        ))

        if not user_query:
            return func.HttpResponse(json.dumps({"error": "User not found"}), status_code=404, mimetype="application/json")

        user_doc = user_query[0]

        # Validate OTP
        stored_otp = user_doc.get("reset_otp")
        otp_expiry = user_doc.get("otp_expiry")

        if not stored_otp or not otp_expiry:
            return func.HttpResponse(json.dumps({"error": "No OTP request found"}), status_code=400, mimetype="application/json")

        # Check OTP validity
        if stored_otp != otp:
            return func.HttpResponse(json.dumps({"error": "Invalid OTP"}), status_code=400, mimetype="application/json")

        if datetime.datetime.utcnow() > datetime.datetime.fromisoformat(otp_expiry):
            return func.HttpResponse(json.dumps({"error": "OTP expired"}), status_code=400, mimetype="application/json")

        # Validate new password length
        if not (8 <= len(new_password) <= 15):
            return func.HttpResponse(json.dumps({"error": "Password must be between 8 and 15 characters"}), status_code=400, mimetype="application/json")

        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

        # Update user password and clear OTP
        user_doc["password"] = hashed_password.decode("utf-8")
        user_doc.pop("reset_otp", None)
        user_doc.pop("otp_expiry", None)

        user_container.upsert_item(user_doc)

        # Optionally, send a confirmation email about password reset
        subject = "Your Password Has Been Reset"
        body_text = (
            f"Hello {user_doc['username']},\n\n"
            "Your password has been successfully reset.\n\n"
            "If you did not perform this action, please contact our support team immediately.\n\n"
            "Best regards,\nCalendar App"
        )
        send_email(user_doc["email"], subject, body_text)

        return func.HttpResponse(json.dumps({"message": "Password reset successful"}), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.exception("Error in reset_password: %s", str(e))
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")
