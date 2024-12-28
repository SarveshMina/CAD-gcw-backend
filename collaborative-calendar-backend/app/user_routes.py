# app/user_routes.py

import logging
import bcrypt
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError

from app.database import user_container, calendars_container
from app.models import User, Calendar
from app.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Register a new user
def register_user(user_data: User):
    logger.info("Received request to register user: %s", user_data.username)

    # Validate username length (5..15)
    if not (5 <= len(user_data.username) <= 15):
        logger.warning("Username '%s' invalid length", user_data.username)
        return {"error": "Username must be between 5 and 15 characters"}, 400

    # Validate password length (8..15)
    if not (8 <= len(user_data.password) <= 15):
        logger.warning("Password for '%s' invalid length", user_data.username)
        return {"error": "Password must be between 8 and 15 characters"}, 400

    # Check if user already exists
    existing_user = list(
        user_container.query_items(
            query="SELECT * FROM Users u WHERE u.username = @username",
            parameters=[{"name": "@username", "value": user_data.username}],
            enable_cross_partition_query=True
        )
    )
    if existing_user:
        logger.info("Username '%s' already exists in DB", user_data.username)
        return {"error": "Username already exists"}, 400

    # Hash the password
    hashed_password = bcrypt.hashpw(
        user_data.password.encode("utf-8"), bcrypt.gensalt()
    )
    user_data.password = hashed_password.decode("utf-8")

    # Create the user record in Cosmos DB
    try:
        user_item = user_data.dict()
        user_item["id"] = user_data.userId  # Cosmos DB 'id' fix
        user_container.create_item(user_item)

        # Create home calendar for this user
        home_cal = Calendar(
            name=f"{user_data.username}'s Home Calendar",
            ownerId=user_data.userId,
            isGroup=False,
            members=[user_data.userId]
        )
        cal_item = home_cal.dict()
        cal_item["id"] = home_cal.calendarId  # 'id' fix for Cosmos
        calendars_container.create_item(cal_item)

        # Update the user's calendars list
        user_data.calendars.append(home_cal.calendarId)
        user_container.upsert_item(user_data.dict())  # or replace_item if needed

        logger.info("User '%s' created successfully with home calendar '%s'",
                    user_data.username, home_cal.calendarId)
        return {"message": "User registered successfully", # Return user ID and calendar ID
                "userId": user_data.userId,
                "homeCalendarId": home_cal.calendarId}, 201
    
    # Handle exceptions
    except CosmosResourceExistsError:
        logger.exception("User resource conflict in DB for '%s'", user_data.username)
        return {"error": "User already exists"}, 400
    except CosmosHttpResponseError as e: # Cosmos DB HTTP error
        logger.exception("Cosmos HTTP error for '%s': %s", user_data.username, str(e))
        return {"error": str(e)}, 500

# Login a user
def login_user(username: str, password: str):
    logger.info("Received login request for username: %s", username)
    # Find the user in Cosmos DB
    user_query = list(
        user_container.query_items(
            query="SELECT * FROM Users u WHERE u.username = @username",
            parameters=[{"name": "@username", "value": username}],
            enable_cross_partition_query=True
        )
    )
    # Check if user exists
    if not user_query:
        logger.warning("Login failed: user '%s' not found", username)
        return {"error": "User not found"}, 404
    
    # Get the user record
    user = user_query[0]

    # Check the password
    if bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        logger.info("User '%s' logged in successfully", username)
        return {"message": "Login successful", "userId": user["userId"]}, 200
    else: # Invalid password
        logger.warning("Invalid credentials for user '%s'", username)
        return {"error": "Invalid credentials"}, 401
