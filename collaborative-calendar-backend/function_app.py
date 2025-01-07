# function_app.py

import azure.functions as func
from app.main import (
    register, login,
    create_event, list_events,
    create_group, add_user_to_group, remove_user_from_group,
    func_create_personal_calendar, delete_personal,
    update_event_handler, delete_event_handler
)

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

# Personal Calendar Endpoints
@app.route(route="personal-calendar/create", methods=["POST"])
def create_personal_function(req: func.HttpRequest) -> func.HttpResponse:
    return func_create_personal_calendar(req)

@app.route(route="personal-calendar/{calendar_id}/delete", methods=["POST"])
def delete_personal_function(req: func.HttpRequest) -> func.HttpResponse:
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
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
