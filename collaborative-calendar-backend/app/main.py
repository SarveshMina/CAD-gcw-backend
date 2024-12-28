# app/main.py

from azure.functions import HttpRequest, HttpResponse
import json
import logging

from app.user_routes import register_user, login_user
from app.calendar_routes import add_event, get_events
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
    try:
        req_body = req.get_json()
        username = req_body.get("username")
        password = req_body.get("password")

        if not username or not password:
            return HttpResponse(json.dumps({"error": "Missing credentials"}), status_code=400)

        response, status_code = login_user(username, password)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in login endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def create_event(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    The actual handler for creating an event, invoked by create_event_function in function_app.py
    """
    try:
        event_data = req.get_json()
        response, status_code = add_event(calendar_id, event_data)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in create_event: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def list_events(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    The actual handler for listing events, invoked by list_events_function in function_app.py
    """
    try:
        response, status_code = get_events(calendar_id)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in list_events: %s", str(e))
        return HttpResponse(str(e), status_code=500)
