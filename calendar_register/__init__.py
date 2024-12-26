import logging
import uuid
import json
import azure.functions as func
from ..cosmos_db_helper import get_cosmos_container, query_users

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    container = get_cosmos_container()
    if container is None:
        return func.HttpResponse(json.dumps({"result": False, "msg": "Database connection error."}), status_code=500, mimetype="application/json")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON input.", status_code=400)

    username = req_body.get("username")
    password = req_body.get("password")

    if not (5 <= len(username) <= 15):
        return func.HttpResponse(json.dumps({"result": False, "msg": "Username must be 5-15 characters long."}), status_code=400, mimetype="application/json")

    if not (8 <= len(password) <= 15):
        return func.HttpResponse(json.dumps({"result": False, "msg": "Password must be 8-15 characters long."}), status_code=400, mimetype="application/json")

    existing_users = query_users(container, username)
    if existing_users is None: # Check if query failed
        return func.HttpResponse(json.dumps({"result": False, "msg": "Error checking for existing user."}), status_code=500, mimetype="application/json")

    if existing_users:
        return func.HttpResponse(json.dumps({"result": False, "msg": "Username already exists."}), status_code=409, mimetype="application/json")

    user_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password": password,  # Hash this in production!
        "calendars": [],
        "groups": [],
    }

    try:
        container.create_item(body=user_data)
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Failed to create item in CosmosDB: {str(e)}")
        return func.HttpResponse(json.dumps({"result": False, "msg": "Error creating user profile."}), status_code=500, mimetype="application/json")

    return func.HttpResponse(json.dumps({"result": True, "msg": "Registration successful."}), status_code=201, mimetype="application/json")