# function_app.py

import azure.functions as func
from app.main import (
    register, login,
    create_event, list_events,
    create_group, add_user_to_group, remove_user_from_group,
    func_create_personal_calendar, delete_personal,
    update_event_handler, delete_event_handler,
    get_user_id_handler, get_all_events_handler,
    edit_group_calendar_handler, leave_group_calendar_handler
)
from app.calendar_routes import get_user_calendars, send_message_to_group  # Import the chat function
import logging
import json

app = func.FunctionApp()

@app.route(route="register", methods=["POST"])
def register_function(req: func.HttpRequest) -> func.HttpResponse:
    return register(req)

@app.route(route="login", methods=["POST"])
def login_function(req: func.HttpRequest) -> func.HttpResponse:
    return login(req)

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
    """
    GET /user/{user_id}/calendars
    Returns all calendars where the user is a member.
    """
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


# Group Chat Endpoints
@app.route(route="group-calendar/{calendar_id}/send-message", methods=["POST"])
def send_group_message_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint to send a chat message to a group calendar.
    Expects JSON body with 'userId' and 'message'.
    """
    calendar_id = req.route_params.get("calendar_id")
    logger = logging.getLogger(__name__)
    
    try:
        body = req.get_json()
        user_id = body.get("userId")
        message = body.get("message")
        
        if not user_id or not message:
            return func.HttpResponse(
                json.dumps({"error": "Missing userId or message in request body."}),
                status_code=400,
                mimetype="application/json"
            )
        
        response, status_code = send_message_to_group(calendar_id, user_id, message)
        return func.HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in send_group_message endpoint: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )