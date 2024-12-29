# app/main.py

from azure.functions import HttpRequest, HttpResponse
import json
import logging

from app.user_routes import register_user, login_user
from app.calendar_routes import (
    add_event, get_events,
    create_group_calendar, add_user_to_group_calendar, remove_user_from_group_calendar,
    create_personal_calendar, delete_personal_calendar
)

from app.calendar_routes import update_event, delete_event

from app.auth import token_required

from app.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def register(req: HttpRequest) -> HttpResponse:
    try:
        req_body = req.get_json()
        user = User(**req_body)
        response, status_code = register_user(user)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in register endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def login(req: HttpRequest) -> HttpResponse:
    # Login does not require authentication
    try:
        req_body = req.get_json()
        username = req_body.get("username")
        password = req_body.get("password")

        if not username or not password:
            return HttpResponse(json.dumps({"error": "Missing credentials"}), status_code=400, mimetype="application/json")

        response, status_code = login_user(username, password)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in login endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

@token_required
def create_event(req: HttpRequest, calendar_id: str, user_id: str) -> HttpResponse:
    """
    Called from function_app.py's create_event_function
    which extracts 'calendar_id' from req.route_params.
    """
    try:
        logger.info("Create event endpoint hit for calendar %s by user %s", calendar_id, user_id)
        event_data = req.get_json()

        # Optionally, enforce that the user is a member of the calendar
        response, status_code = add_event(calendar_id, event_data, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in create_event endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

@token_required
def list_events(req: HttpRequest, calendar_id: str, user_id: str) -> HttpResponse:
    """
    Called from function_app.py's list_events_function.
    """
    try:
        logger.info("List events endpoint hit for calendar %s by user %s", calendar_id, user_id)
        response, status_code = get_events(calendar_id, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in list_events endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")
    
@token_required
def update_event_handler(req: HttpRequest, calendar_id: str, event_id: str, user_id: str) -> HttpResponse:
    """
    Updates an existing event in a calendar.
    """
    try:
        updated_data = req.get_json()
        response, status_code = update_event(calendar_id, event_id, updated_data, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in update_event_handler: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

@token_required
def delete_event_handler(req: HttpRequest, calendar_id: str, event_id: str, user_id: str) -> HttpResponse:
    """
    Deletes an event from a calendar.
    """
    try:
        response, status_code = delete_event(calendar_id, event_id, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in delete_event_handler: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

# -----------------------------
# Group Calendar Endpoints
# -----------------------------
def create_group(req: HttpRequest) -> HttpResponse:
    """
    Example request body:
    {
      "ownerId": "someUserId",
      "name": "CAD Project Group",
      "members": ["otherUserId1", "otherUserId2"]
    }
    """
    try:
        body = req.get_json()
        owner_id = body.get("ownerId")
        name = body.get("name")
        members = body.get("members", [])

        if not owner_id or not name:
            return HttpResponse(json.dumps({"error": "Missing ownerId or name"}), status_code=400)

        response, status_code = create_group_calendar(owner_id, name, members)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in create_group endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def add_user_to_group(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    Expects request body:
    {
      "adminId": "theAdminUserId",
      "userId": "theUserToAdd"
    }
    """
    try:
        body = req.get_json()
        admin_id = body.get("adminId")
        user_id = body.get("userId")

        if not admin_id or not user_id:
            return HttpResponse(json.dumps({"error": "Missing adminId or userId"}), status_code=400)

        response, status_code = add_user_to_group_calendar(calendar_id, admin_id, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in add_user_to_group endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def remove_user_from_group(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    Expects request body:
    {
      "adminId": "theAdminUserId",
      "userId": "theUserToRemove"
    }
    """
    try:
        body = req.get_json()
        admin_id = body.get("adminId")
        user_id = body.get("userId")

        if not admin_id or not user_id:
            return HttpResponse(json.dumps({"error": "Missing adminId or userId"}), status_code=400)

        response, status_code = remove_user_from_group_calendar(calendar_id, admin_id, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in remove_user_from_group endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

# -----------------------------
# Personal Calendar Endpoints
# -----------------------------
def create_personal(req: HttpRequest) -> HttpResponse:
    """
    Creates a new personal calendar for a user.
    Example request body:
    {
      "userId": "someUserId",
      "name": "Work Calendar"
    }
    """
    try:
        body = req.get_json()
        user_id = body.get("userId")
        name = body.get("name")

        if not user_id or not name:
            return HttpResponse(json.dumps({"error": "Missing userId or name"}), status_code=400)

        response, status_code = create_personal_calendar(user_id, name)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in create_personal endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def delete_personal(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    Deletes a personal calendar.
    Example request body:
    {
      "userId": "someUserId"
    }
    """
    try:
        body = req.get_json()
        user_id = body.get("userId")

        if not user_id:
            return HttpResponse(json.dumps({"error": "Missing userId"}), status_code=400)

        response, status_code = delete_personal_calendar(user_id, calendar_id)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in delete_personal endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)
