import logging
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
        return func.HttpResponse(json.dumps({"result": False, "msg": "Invalid JSON input."}), status_code=400, mimetype="application/json")

    username = req_body.get("username")
    password = req_body.get("password")

    if not username or not password:
        return func.HttpResponse(json.dumps({"result": False, "msg": "Username and password are required."}), status_code=400, mimetype="application/json")

    existing_users = query_users(container, username)
    if existing_users is None: # Check if query failed
        return func.HttpResponse(json.dumps({"result": False, "msg": "Error checking for existing user."}), status_code=500, mimetype="application/json")

    if existing_users:
        stored_user = existing_users[0]
        if stored_user.get("password") == password:  # Compare stored password with provided password (Hash in production!)
            return func.HttpResponse(json.dumps({"result": True, "msg": "Login successful."}), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps({"result": False, "msg": "Invalid username or password."}), status_code=401, mimetype="application/json")
    else:
        return func.HttpResponse(json.dumps({"result": False, "msg": "Invalid username or password."}), status_code=401, mimetype="application/json")