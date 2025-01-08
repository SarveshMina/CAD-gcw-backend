# app/user_routes.py

import logging
import bcrypt
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
import os
from dotenv import load_dotenv

from app.database import user_container, calendars_container
from app.models import User, Calendar

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def register_user(user_data: User):
    logger.info("Received request to register user: %s", user_data.username)
    logger.info("DEBUG: user_data.__fields__ => %s", list(User.__fields__.keys()))
    # ^ This debug line is optional but helps confirm you see "default_calendar_id".

    # Validate username & password
    if not (5 <= len(user_data.username) <= 15):
        return {"error": "Username must be between 5 and 15 characters"}, 400

    if not (8 <= len(user_data.password) <= 15):
        return {"error": "Password must be between 8 and 15 characters"}, 400

    # Check if user exists
    existing_user = list(
        user_container.query_items(
            query="SELECT * FROM Users u WHERE u.username = @username",
            parameters=[{"name": "@username", "value": user_data.username}],
            enable_cross_partition_query=True
        )
    )
    if existing_user:
        return {"error": "Username already exists"}, 400

    # Hash
    hashed_password = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
    user_data.password = hashed_password.decode("utf-8")

    # Build doc
    user_item = user_data.dict()
    user_item["id"] = user_data.userId

    try:
        # Create user doc
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
        home_cal_dict["id"] = home_cal.calendarId
        home_cal_dict["color"] = "blue"  # default color is "blue" here

        calendars_container.create_item(body=home_cal_dict)

        # Set up default_calendar_id
        user_data.calendars.append(home_cal.calendarId)
        user_data.default_calendar_id = home_cal.calendarId

        # Upsert updated doc
        updated_user_item = user_data.dict()
        updated_user_item["id"] = user_data.userId
        user_container.upsert_item(body=updated_user_item)

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


def get_default_calendar_id(user_id: str):
    try:
        user_query = list(
            user_container.query_items(
                query="SELECT * FROM Users u WHERE u.userId = @userId",
                parameters=[{"name": "@userId", "value": user_id}],
                enable_cross_partition_query=True
            )
        )
        if not user_query:
            return None

        user_doc = user_query[0]
        return user_doc.get("default_calendar_id", "")
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching default calendar for user '%s': %s", user_id, str(e))
        return None


def login_user(username: str, password: str):
    logger.info("Received login request for username: %s", username)

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
