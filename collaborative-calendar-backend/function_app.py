# function_app.py

import azure.functions as func
import logging
import json

from app.main import (
    register, login,
    create_event, list_events,
    create_group, add_user_to_group, remove_user_from_group,
    func_create_personal_calendar, delete_personal,
    update_event_handler, delete_event_handler,
    get_user_id_handler, get_all_events_handler,
    edit_group_calendar_handler, leave_group_calendar_handler,
    update_user_handler, delete_group_calendar_handler
)
from app.user_routes import google_oauth_login
from app.utils import get_client_ip, get_geolocation
from app.calendar_routes import import_internet_calendar
from pydantic import ValidationError
from app.models import User
from app.user_routes import login_user, register_user


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure that handlers are added only once
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = func.FunctionApp()

@app.route(route="register", methods=["POST"])
def register_function(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        user = User(**req_body)
        client_ip = get_client_ip(req)
        location = get_geolocation(client_ip)
        
        response, status_code = register_user(user, client_ip, location)
        return func.HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except ValidationError as ve:
        logger.exception("Validation error in register endpoint: %s", str(ve))
        return func.HttpResponse(json.dumps({"error": str(ve)}), status_code=422, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in register endpoint: %s", str(e))
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


@app.route(route="login", methods=["POST"])
def login_function(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        username = req_body.get("username")
        password = req_body.get("password")

        if not username or not password:
            return func.HttpResponse(
                json.dumps({"error": "Missing credentials"}),
                status_code=400,
                mimetype="application/json"
            )
        
        client_ip = get_client_ip(req)
        location = get_geolocation(client_ip)
        
        response, status_code = login_user(username, password, client_ip, location)
        return func.HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except ValidationError as ve:
        logger.exception("Validation error in login endpoint: %s", str(ve))
        return func.HttpResponse(json.dumps({"error": str(ve)}), status_code=422, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in login endpoint: %s", str(e))
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


@app.route(route="user/{user_id}/profile", methods=["GET"])
def get_user_profile(req: func.HttpRequest) -> func.HttpResponse:
    import json
    from app.database import user_container
    import azure.functions as func

    try:
        user_id = req.route_params.get("user_id")
        user_query = list(
            user_container.query_items(
                query="SELECT * FROM Users u WHERE u.userId = @userId",
                parameters=[{"name": "@userId", "value": user_id}],
                enable_cross_partition_query=True
            )
        )
        if not user_query:
            return func.HttpResponse(
                json.dumps({"error": "User not found"}),
                status_code=404,
                mimetype="application/json"
            )

        user_doc = user_query[0]
        user_profile = {
            "username": user_doc.get("username", ""),
            "email": user_doc.get("email", "")
        }
        return func.HttpResponse(
            json.dumps(user_profile),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="calendar/{calendar_id}/event", methods=["POST"])
def create_event_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return create_event(req, calendar_id)

@app.route(route="calendar/{calendar_id}/events", methods=["GET"])
def list_events_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return list_events(req, calendar_id)

@app.route(route="calendar/{calendar_id}/event/{event_id}/update", methods=["PUT"])
def update_event_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    event_id = req.route_params.get("event_id")
    return update_event_handler(req, calendar_id, event_id)

@app.route(route="calendar/{calendar_id}/event/{event_id}/delete", methods=["DELETE"])
def delete_event_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    event_id = req.route_params.get("event_id")
    return delete_event_handler(req, calendar_id, event_id)

@app.route(route="user/{user_id}/events", methods=["GET"])
def get_all_events_function(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.route_params.get("user_id")
    return get_all_events_handler(req, user_id)

@app.route(route="user/{username}/id", methods=["GET"])
def get_user_id_function(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get("username")
    return get_user_id_handler(req, username)

# Group Calendar Endpoints
@app.route(route="group-calendar/create", methods=["POST"])
def create_group_function(req: func.HttpRequest) -> func.HttpResponse:
    return create_group(req)

@app.route(route="group-calendar/{calendar_id}/add-user", methods=["POST"])
def add_user_to_group_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return add_user_to_group(req, calendar_id)

@app.route(route="group-calendar/{calendar_id}/remove-user", methods=["POST"])
def remove_user_from_group_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return remove_user_from_group(req, calendar_id)

@app.route(route="group-calendar/{calendar_id}/edit", methods=["PUT"])
def edit_group_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return edit_group_calendar_handler(req, calendar_id)

@app.route(route="group-calendar/{calendar_id}/leave", methods=["POST"])
def leave_group_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return leave_group_calendar_handler(req, calendar_id)

# Personal Calendar Endpoints
@app.route(route="personal-calendar/create", methods=["POST"])
def create_personal_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    return func_create_personal_calendar(req)

@app.route(route="personal-calendar/{calendar_id}/delete", methods=["POST"])
def delete_personal_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return delete_personal(req, calendar_id)

@app.route(route="user/{user_id}/calendars", methods=["GET"])
def list_user_calendars(req: func.HttpRequest) -> func.HttpResponse:
    from app.calendar_routes import get_user_calendars
    import json
    import logging

    logger = logging.getLogger(__name__)

    try:
        user_id = req.route_params.get("user_id")
        response, status_code = get_user_calendars(user_id)
        return func.HttpResponse(
            json.dumps(response),
            status_code=status_code,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error in list_user_calendars endpoint: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="user/{user_id}", methods=["PUT"])
def update_user_function(req: func.HttpRequest) -> func.HttpResponse:
    return update_user_handler(req)

@app.route(route="forgot-password", methods=["POST"])
def forgot_password_function(req: func.HttpRequest) -> func.HttpResponse:
    from app.user_routes import forgot_password_request
    return forgot_password_request(req)

@app.route(route="reset-password", methods=["POST"])
def reset_password_function(req: func.HttpRequest) -> func.HttpResponse:
    from app.user_routes import reset_password
    try:
        client_ip = get_client_ip(req)
        location = get_geolocation(client_ip)
        return reset_password(req, client_ip, location)
    except Exception as e:
        logger.exception("Error in reset_password_handler: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="personal-calendar/{calendar_id}/edit", methods=["PUT"])
def edit_personal_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    from app.calendar_routes import edit_personal_calendar
    calendar_id = req.route_params.get("calendar_id")
    updated_data = req.get_json()
    user_id = req.headers.get("user_id")
    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "User ID is required"}),
            status_code=400,
            mimetype="application/json"
        )
    response_body, status_code = edit_personal_calendar(calendar_id, user_id, updated_data)
    return func.HttpResponse(
        body=json.dumps(response_body),
        status_code=status_code,
        mimetype="application/json"
    )

@app.route(route="group-calendar/{calendar_id}/delete", methods=["POST"])
def delete_group_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return delete_group_calendar_handler(req, calendar_id)

@app.route(route="calendar/import", methods=["POST"])
def import_calendar_function(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        user_id = body.get("userId")
        ical_url = body.get("iCalURL")
        name = body.get("name", '')
        color = body.get("color", 'blue')
        if not user_id or not ical_url:
            return func.HttpResponse(
                json.dumps({"error": "Missing userId or iCalURL in request body."}),
                status_code=400,
                mimetype="application/json"
            )
        from app.calendar_routes import import_internet_calendar
        response_body, status_code = import_internet_calendar(user_id, ical_url, name, color)
        return func.HttpResponse(
            json.dumps(response_body),
            status_code=status_code,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error in import_calendar_function: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="auth/google", methods=["POST"])
def google_auth_function(req: func.HttpRequest) -> func.HttpResponse:
    import json
    import logging
    
    logger = logging.getLogger(__name__)

    try:
        body = req.get_json()
        id_token_str = body.get("idToken")
        if not id_token_str:
            return func.HttpResponse(
                json.dumps({"error": "Missing idToken in request body."}),
                status_code=400,
                mimetype="application/json"
            )
        
        client_ip = get_client_ip(req)
        location = get_geolocation(client_ip)
        response, status_code = google_oauth_login(id_token_str, client_ip, location)
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=status_code,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error in google_auth_function: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
