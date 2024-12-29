# function_app.py

import azure.functions as func
from app.main import (
    register, login,
    create_event, list_events,
    create_group, add_user_to_group, remove_user_from_group,
    create_personal, delete_personal,
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
    """
    We do NOT define 'calendar_id' as a function parameter.
    Instead, we retrieve it from req.route_params inside the function.
    """
    calendar_id = req.route_params.get("calendar_id")
    return create_event(req, calendar_id)

@app.route(route="calendar/{calendar_id}/events", methods=["GET"])
def list_events_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get("calendar_id")
    return list_events(req, calendar_id)

@app.route(route="calendar/{calendar_id}/event/{event_id}/update", methods=["PUT"])
def update_event_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    PUT /calendar/{calendar_id}/event/{event_id}/update
    Body example:
    {
      "title": "Updated Meeting Title",
      "description": "Updated description."
    }
    """
    calendar_id = req.route_params.get("calendar_id")
    event_id = req.route_params.get("event_id")
    return update_event_handler(req, calendar_id, event_id)

@app.route(route="calendar/{calendar_id}/event/{event_id}/delete", methods=["DELETE"])
def delete_event_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    DELETE /calendar/{calendar_id}/event/{event_id}/delete
    """
    calendar_id = req.route_params.get("calendar_id")
    event_id = req.route_params.get("event_id")
    return delete_event_handler(req, calendar_id, event_id)

# -----------------------------
# Group Calendar Endpoints
# -----------------------------
@app.route(route="group-calendar/create", methods=["POST"])
def create_group_function(req: func.HttpRequest) -> func.HttpResponse:
    return create_group(req)

@app.route(route="group-calendar/{calendar_id}/add-user", methods=["POST"])
def add_user_to_group_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /group-calendar/{calendar_id}/add-user
    Body example:
    {
      "adminId": "theAdminUserId",
      "userId": "theUserToAdd"
    }
    """
    calendar_id = req.route_params.get("calendar_id")
    return add_user_to_group(req, calendar_id)

@app.route(route="group-calendar/{calendar_id}/remove-user", methods=["POST"])
def remove_user_from_group_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /group-calendar/{calendar_id}/remove-user
    Body example:
    {
      "adminId": "theAdminUserId",
      "userId": "theUserToRemove"
    }
    """
    calendar_id = req.route_params.get("calendar_id")
    return remove_user_from_group(req, calendar_id)

# -----------------------------
# Personal Calendar Endpoints
# -----------------------------
@app.route(route="personal-calendar/create", methods=["POST"])
def create_personal_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Example:
    POST /personal-calendar/create
    {
      "userId": "someUserId",
      "name": "Work Calendar"
    }
    """
    return create_personal(req)

@app.route(route="personal-calendar/{calendar_id}/delete", methods=["POST"])
def delete_personal_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    Example:
    POST /personal-calendar/{calendar_id}/delete
    {
      "userId": "someUserId"
    }
    """
    calendar_id = req.route_params.get("calendar_id")
    return delete_personal(req, calendar_id)
