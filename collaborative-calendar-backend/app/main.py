from azure.functions import HttpRequest, HttpResponse
import json
import logging
from pydantic import ValidationError
import azure.functions as func

from app.user_routes import register_user, login_user, update_user_profile
from app.calendar_routes import (
    add_event, get_events,
    create_group_calendar, add_user_to_group_calendar, remove_user_from_group_calendar,
    create_personal_calendar, delete_personal_calendar,
    update_event, delete_event, get_user_id, get_all_events_for_user,
    edit_group_calendar, leave_group_calendar,
    delete_group_calendar, import_internet_calendar
)

from app.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def register(req: HttpRequest) -> HttpResponse:
    try:
        req_body = req.get_json()
        user = User(**req_body)
        client_ip = req.headers.get("X-Forwarded-For", req.headers.get("REMOTE_ADDR", ""))
        location = req.url
        response, status_code = register_user(user, client_ip, location)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except ValidationError as ve:
        logger.exception("Validation error in register endpoint: %s", str(ve))
        return HttpResponse(json.dumps({"error": str(ve)}), status_code=422, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in register endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

def login(req: HttpRequest) -> HttpResponse:
    try:
        req_body = req.get_json()
        username = req_body.get("username")
        password = req_body.get("password")
        client_ip = req.headers.get("X-Forwarded-For", req.headers.get("REMOTE_ADDR", ""))

        if not username or not password:
            return HttpResponse(
                json.dumps({"error": "Missing credentials"}),
                status_code=400,
                mimetype="application/json"
            )

        response, status_code = login_user(username, password, client_ip, location="req.url")
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in login endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


# Add the new user update handler
def update_user_handler(req: HttpRequest) -> HttpResponse:
    try:
        user_id = req.route_params.get("user_id")
        updates = req.get_json()
        response, status_code = update_user_profile(user_id, updates)
        return HttpResponse(
            json.dumps(response),
            status_code=status_code,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error in update_user_handler: %s", str(e))
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    

def get_all_events_handler(req: HttpRequest, user_id: str) -> HttpResponse:
    """
    Handler to get all events across all calendars the user is a member of.
    GET /user/{user_id}/events
    Returns { events: [...] }
    """
    try:
        events = get_all_events_for_user(user_id)
        return HttpResponse(
            json.dumps({"events": events}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error in get_all_events_handler: %s", str(e))
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
def edit_group_calendar_handler(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    Handler to edit group calendar's name and color.
    Expects JSON body with fields to update: name and/or color.
    """
    try:
        body = req.get_json()
        admin_id = body.get("adminId")  # Assuming adminId is sent in the request body
        if not admin_id:
            return HttpResponse(
                json.dumps({"error": "Missing adminId in request body."}),
                status_code=400,
                mimetype="application/json"
            )
        updated_data = {}
        if "name" in body:
            updated_data["name"] = body["name"]
        if "color" in body:
            updated_data["color"] = body["color"]
        if not updated_data:
            return HttpResponse(
                json.dumps({"error": "No valid fields to update."}),
                status_code=400,
                mimetype="application/json"
            )
        response, status_code = edit_group_calendar(calendar_id, admin_id, updated_data)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in edit_group_calendar endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def leave_group_calendar_handler(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    Handler for a user to leave a group calendar.
    Expects JSON body with 'userId'.
    """
    try:
        body = req.get_json()
        user_id = body.get("userId")
        if not user_id:
            return HttpResponse(
                json.dumps({"error": "Missing userId in request body."}),
                status_code=400,
                mimetype="application/json"
            )
        response, status_code = leave_group_calendar(calendar_id, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in leave_group_calendar_handler: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


# Instead of @token_required, we just allow calls.
# We'll assume we get userId from the request body for membership checks, or we skip them entirely.
def create_event(req: HttpRequest, calendar_id: str) -> HttpResponse:
    try:
        req_body = req.get_json()
        user_id = req_body.get("userId")  # Ensure userId is provided in the request body
        if not user_id:
            return HttpResponse(
                json.dumps({"error": "Missing userId in request body."}),
                status_code=400,
                mimetype="application/json"
            )
        logger.info("Create event endpoint for calendar %s by user %s", calendar_id, user_id)

        response, status_code = add_event(calendar_id, req_body, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in create_event endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def list_events(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    GET /calendar/{calendar_id}/events?userId=<...>
    """
    try:
        # 1) userId from query param (if needed):
        user_id = req.params.get("userId", "")

        # 2) (Optional) If you *require* userId, you can do a quick check:
        # if not user_id:
        #     return HttpResponse(
        #         json.dumps({"error": "Missing userId query param"}),
        #         status_code=400,
        #         mimetype="application/json"
        #     )

        logger.info("List events endpoint for calendar %s by user %s", calendar_id, user_id)

        # 3) Pass the calendarId & userId to your DB function
        #    (assuming get_events(...) is defined & checks membership).
        response, status_code = get_events(calendar_id, user_id)

        # 4) Return result
        return HttpResponse(
            json.dumps(response),
            status_code=status_code,
            mimetype="application/json"
        )

    except Exception as e:
        logger.exception("Error in list_events endpoint: %s", str(e))
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )




def update_event_handler(req: HttpRequest, calendar_id: str, event_id: str) -> HttpResponse:
    try:
        req_body = req.get_json()
        user_id = req_body.get("userId") 
        response, status_code = update_event(calendar_id, event_id, req_body, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in update_event_handler: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def delete_event_handler(req: HttpRequest, calendar_id: str, event_id: str) -> HttpResponse:
    try:
        req_body = req.get_json()
        user_id = req_body.get("userId")
        response, status_code = delete_event(calendar_id, event_id, user_id)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in delete_event_handler: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def create_group(req: HttpRequest) -> HttpResponse:
    """
    Endpoint to create a group calendar.
    Expects JSON body with:
    - ownerId: str
    - name: str
    - members: list of usernames (max 4)
    - color: str (optional but required by create_group_calendar)
    """
    try:
        body = req.get_json()
        owner_id = body.get("ownerId")
        name = body.get("name")
        members_usernames = body.get("members", [])
        # Extract color from request (fallback to one of your allowed colors if not present)
        color = body.get("color", "pink")

        # Basic validation
        if not owner_id or not name:
            return HttpResponse(
                json.dumps({"error": "Missing ownerId or name"}),
                status_code=400,
                mimetype="application/json"
            )

        if not isinstance(members_usernames, list):
            return HttpResponse(
                json.dumps({"error": "Members should be a list of usernames"}),
                status_code=400,
                mimetype="application/json"
            )

        if len(members_usernames) > 4:
            return HttpResponse(
                json.dumps({"error": "Cannot add more than 4 members to the group calendar"}),
                status_code=400,
                mimetype="application/json"
            )

        # Pass color to create_group_calendar
        response, status_code = create_group_calendar(owner_id, name, members_usernames, color)
        return HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in create_group endpoint: %s", str(e))
        return HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

def get_user_id_handler(req: HttpRequest, username: str) -> HttpResponse:
    """
    Handler to get userId based on username.
    GET /user/{username}/id
    """
    try:
        user_id = get_user_id(username)
        if user_id:
            return HttpResponse(
                json.dumps({"userId": user_id}),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return HttpResponse(
                json.dumps({"error": f"User '{username}' does not exist."}),
                status_code=404,
                mimetype="application/json"
            )
    except Exception as e:
        logger.exception("Error in get_user_id_handler: %s", str(e))
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

def add_user_to_group(req: HttpRequest, calendar_id: str) -> HttpResponse:
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

def func_create_personal_calendar(req: HttpRequest) -> HttpResponse:
    try:
        body = req.get_json()
        user_id = body.get("userId")
        name = body.get("name")
        # Extract color from the request body (default it if not present)
        color = body.get("color", "pink")  # or your desired default color

        if not user_id or not name:
            return HttpResponse(
                json.dumps({"error": "Missing userId or name"}),
                status_code=400,
                mimetype="application/json"
            )

        # Now pass color to create_personal_calendar
        response, status_code = create_personal_calendar(user_id, name, color)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in create_personal endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)


def delete_personal(req: HttpRequest, calendar_id: str) -> HttpResponse:
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
    
def delete_group_calendar_handler(req: HttpRequest, calendar_id: str) -> HttpResponse:
    """
    Handler to delete a group calendar.
    Expects JSON body with 'adminId'.
    """
    try:
        body = req.get_json()
        admin_id = body.get("adminId")

        if not admin_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing adminId in request body."}),
                status_code=400,
                mimetype="application/json"
            )

        response, status_code = remove_user_from_group_calendar(calendar_id, admin_id, admin_id)
        if status_code == 200:
            # Now delete the group calendar
            response, status_code = delete_group_calendar(calendar_id, admin_id)
        
        return func.HttpResponse(json.dumps(response), status_code=status_code, mimetype="application/json")
    except Exception as e:
        logger.exception("Error in delete_group_calendar_handler: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )



    

def import_calendar(req: HttpRequest) -> HttpResponse:
    """
    Handler to import an internet calendar (iCal feed) for a user.
    Expects JSON body with:
    - userId: str
    - iCalURL: str
    """
    try:
        body = req.get_json()
        user_id = body.get("userId")
        ical_url = body.get("iCalURL")
        color = body.get("color", "pink")  # or your desired default color
        name = body.get("name", "Imported Calendar")  # or your desired default name
        

        if not user_id or not ical_url:
            return HttpResponse(
                json.dumps({"error": "Missing userId or iCalURL in request body."}),
                status_code=400,
                mimetype="application/json"
            )

        response, status_code = import_internet_calendar(user_id, ical_url, name, color)
        return HttpResponse(
            json.dumps(response),
            status_code=status_code,
            mimetype="application/json"
        )

    except Exception as e:
        logger.exception("Error in import_calendar handler: %s", str(e))
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )