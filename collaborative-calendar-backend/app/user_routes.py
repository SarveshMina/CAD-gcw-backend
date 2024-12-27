# app/user_routes.py

import logging
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
import bcrypt

from app.database import user_container
from app.models import User

# Create a module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def register_user(user_data: User):
    """
    Registers a new user with validation:
    - Username must be unique, 5..15 chars
    - Password must be 8..15 chars
    """

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

    # Create user record in Cosmos DB
    try:
        # Fix for Cosmos DB: set the "id" field so that Cosmos doesn't error
        item_dict = user_data.dict()
        item_dict["id"] = user_data.userId

        logger.debug("Creating user item in Cosmos DB: %s", item_dict)
        user_container.create_item(item_dict)

        logger.info("User '%s' created successfully", user_data.username)
        return {"message": "User registered successfully", "userId": user_data.userId}, 201

    except CosmosResourceExistsError:
        logger.exception("User resource conflict in DB for '%s'", user_data.username)
        return {"error": "User already exists"}, 400
    except CosmosHttpResponseError as e:
        logger.exception("Cosmos HTTP error for '%s': %s", user_data.username, str(e))
        return {"error": str(e)}, 500


def login_user(username: str, password: str):
    """
    Logs a user in using username/password. Checks bcrypt hashed password.
    """

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

    user = user_query[0]

    if bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        logger.info("User '%s' logged in successfully", username)
        return {"message": "Login successful", "userId": user["userId"]}, 200
    else:
        logger.warning("Invalid credentials for user '%s'", username)
        return {"error": "Invalid credentials"}, 401
