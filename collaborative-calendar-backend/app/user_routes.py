import logging
import bcrypt
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


from app.database import user_container, calendars_container
from app.models import User, Calendar


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 1800

def register_user(user_data: User):
    """
    Registers a new user:
    - Check username uniqueness
    - Hash password
    - Create 'home' calendar
    - Container partition key for 'Users': /userId
    """

    logger.info("Received request to register user: %s", user_data.username)

    # Validate username length (5..15)
    if not (5 <= len(user_data.username) <= 15):
        return {"error": "Username must be between 5 and 15 characters"}, 400

    # Validate password length (8..15)
    if not (8 <= len(user_data.password) <= 15):
        return {"error": "Password must be between 8 and 15 characters"}, 400

    # Check if user already exists by username
    existing_user = list(
        user_container.query_items(
            query="SELECT * FROM Users u WHERE u.username = @username",
            parameters=[{"name": "@username", "value": user_data.username}],
            enable_cross_partition_query=True
        )
    )
    if existing_user:
        return {"error": "Username already exists"}, 400

    # Hash the password
    hashed_password = bcrypt.hashpw(
        user_data.password.encode("utf-8"), bcrypt.gensalt()
    )
    user_data.password = hashed_password.decode("utf-8")

    # Build user item
    # The container is partitioned by /userId, so the doc must have userId property
    # Also setting "id" to user_data.userId to satisfy the 'id' field in Cosmos
    user_item = user_data.dict()
    user_item["id"] = user_data.userId

    try:
        # 1) Insert the user doc
        user_container.create_item(body=user_item)

        # 2) Create a 'home' calendar marked as default
        home_cal = Calendar(
            name=f"{user_data.username}'s Home Calendar",
            ownerId=user_data.userId,
            isGroup=False,
            isDefault=True,  # Mark as default
            members=[user_data.userId]
        )
        cal_item = home_cal.dict()
        cal_item["id"] = home_cal.calendarId  # Cosmos 'id' fix

        calendars_container.create_item(body=cal_item)

        # Update user's "calendars" list
        user_data.calendars.append(home_cal.calendarId)

        # 3) Upsert the updated user doc
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


def login_user(username: str, password: str):
    """
    Logs in an existing user by checking their hashed password.
    Generates a JWT token upon successful authentication.
    """
    logger.info("Received login request for username: %s", username)

    # Query by username
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
        
        # Create JWT payload
        payload = {
            "userId": user_doc["userId"],
            "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "message": "Login successful",
            "userId": user_doc["userId"],
            "token": token
        }, 200
    else:
        logger.warning("Invalid credentials for user '%s'", username)
        return {"error": "Invalid credentials"}, 401
