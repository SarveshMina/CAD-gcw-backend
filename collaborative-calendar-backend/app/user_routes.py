import logging
import bcrypt
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError

from app.database import user_container, calendars_container
from app.models import User, Calendar

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
    # We'll also set "id" to user_data.userId to satisfy the 'id' field in Cosmos
    user_item = user_data.dict()
    user_item["id"] = user_data.userId

    try:
        # 1) Insert the user doc (no partition_key=...),
        #    The library will infer the partition key from user_item["userId"].
        user_container.create_item(body=user_item)

        # 2) Create a 'home' calendar
        home_cal = Calendar(
            name=f"{user_data.username}'s home Calendar",
            ownerId=user_data.userId,
            isGroup=False,
            members=[user_data.userId]
        )
        cal_item = home_cal.dict()
        # For 'Calendars' container partitioned by /calendarId
        cal_item["id"] = home_cal.calendarId

        calendars_container.create_item(body=cal_item)
        # The library should infer partition key from cal_item["calendarId"].

        # 3) Update user's "calendars" list
        user_data.calendars.append(home_cal.calendarId)

        # 4) Upsert the updated user doc (again, no partition_key=...),
        #    letting the library infer /userId
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
        return {"message": "Login successful", "userId": user_doc["userId"]}, 200
    else:
        logger.warning("Invalid credentials for user '%s'", username)
        return {"error": "Invalid credentials"}, 401
