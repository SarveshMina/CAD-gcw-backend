# app/calendar_routes.py

import logging
from datetime import datetime
from pydantic import ValidationError
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.database import calendars_container, events_container
from app.models import Event, Calendar

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def add_event(calendar_id: str, event_data: dict):
    logger.info("Adding event to calendar %s", calendar_id)

    # 1) Verify calendar
    try:
        cal_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE c.calendarId = @calId",
            parameters=[{"name":"@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        if not cal_query:
            return {"error": "Calendar not found"}, 404
    except CosmosHttpResponseError as e:
        logger.exception("Error querying calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

    # 2) Create the event doc
    try:
        new_event = Event(**event_data)  # This can raise ValidationError for missing fields
        new_event.calendarId = calendar_id  # Confirm the correct calendarId
        new_event.creatorId = event_data.get("creatorId", "")  # or read from session

        # Convert to dict & set 'id' for Cosmos
        item_dict = new_event.dict()
        item_dict["startTime"] = new_event.startTime.isoformat()
        item_dict["endTime"] = new_event.endTime.isoformat()
        item_dict["id"] = new_event.eventId

        events_container.create_item(item_dict)
        logger.info("Event '%s' created in calendar '%s'", new_event.eventId, calendar_id)
        return {"message": "Event created successfully", "eventId": new_event.eventId}, 201

    except ValidationError as ve:
        # Specific handling for missing/invalid fields
        logger.warning("Validation error for event in calendar '%s': %s", calendar_id, ve)
        return {"error": str(ve)}, 422

    except Exception as e:
        # Catch-all for other issues
        logger.exception("Error creating event in calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

def get_events(calendar_id: str):
    """
    Retrieves all events for a given calendar (by calendarId).
    """
    logger.info("Fetching events for calendar %s", calendar_id)
    try:
        events_query = list(events_container.query_items(
            query="SELECT * FROM Events e WHERE e.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        return {"events": events_query}, 200

    except CosmosHttpResponseError as e:
        logger.exception("Error fetching events for calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500


def create_group_calendar(owner_id: str, name: str, members: list):
    """
    Creates a new group calendar with the specified owner_id (admin) and members.
    The 'owner_id' will be the admin of this group calendar.
    The 'members' list can optionally include other userIds right from creation.
    """
    logger.info("Creating group calendar for owner '%s' with name '%s'", owner_id, name)

    # The admin must always be in the members list:
    if owner_id not in members:
        members.append(owner_id)

    # Create the Calendar model:
    group_cal = Calendar(
        name=name,
        ownerId=owner_id,
        isGroup=True,
        members=members  # includes owner
    )
    cal_item = group_cal.dict()
    cal_item["id"] = group_cal.calendarId  # cosmos 'id' fix

    try:
        calendars_container.create_item(cal_item)
        logger.info("Group calendar '%s' created (ownerId=%s)", group_cal.calendarId, owner_id)
        return {
            "message": "Group calendar created successfully",
            "calendarId": group_cal.calendarId
        }, 201
    except CosmosHttpResponseError as e:
        logger.exception("Error creating group calendar: %s", str(e))
        return {"error": str(e)}, 500


def add_user_to_group_calendar(calendar_id: str, admin_id: str, user_id: str):
    """
    Admin can add 'user_id' to the group calendar's members list.
    We check if 'calendar_id' is a group calendar and if 'admin_id' is the owner.
    """
    logger.info("Admin '%s' is adding user '%s' to group calendar '%s'", admin_id, user_id, calendar_id)

    # 1) Fetch the calendar doc
    try:
        cal_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE c.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        if not cal_query:
            return {"error": "Calendar not found"}, 404
        
        cal_doc = cal_query[0]
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

    # 2) Check if it's a group calendar
    if not cal_doc.get("isGroup"):
        return {"error": "Cannot add user to a personal (non-group) calendar"}, 400
    
    # 3) Check if the admin_id matches ownerId
    if cal_doc.get("ownerId") != admin_id:
        return {"error": "Only the calendar owner can add members"}, 403

    # 4) Add user_id to members list if not already there
    if user_id in cal_doc["members"]:
        logger.info("User '%s' already in the members list", user_id)
        return {"message": "User already in group calendar"}, 200
    else:
        cal_doc["members"].append(user_id)

    # 5) Upsert the updated doc
    try:
        calendars_container.upsert_item(cal_doc)
        logger.info("User '%s' added to group calendar '%s'", user_id, calendar_id)
        return {"message": "User added successfully"}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error updating group calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500


def remove_user_from_group_calendar(calendar_id: str, admin_id: str, user_id: str):
    """
    Admin can remove 'user_id' from the group calendar's members list.
    We check if 'calendar_id' is a group calendar and if 'admin_id' is the owner.
    """
    logger.info("Admin '%s' removing user '%s' from group calendar '%s'", admin_id, user_id, calendar_id)

    # 1) Fetch calendar doc
    try:
        cal_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE c.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        if not cal_query:
            return {"error": "Calendar not found"}, 404
        
        cal_doc = cal_query[0]
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

    # 2) Check if it's group
    if not cal_doc.get("isGroup"):
        return {"error": "Cannot remove user from a personal (non-group) calendar"}, 400

    # 3) Check admin ownership
    if cal_doc.get("ownerId") != admin_id:
        return {"error": "Only the calendar owner can remove members"}, 403

    # 4) Remove user_id if in members
    if user_id not in cal_doc["members"]:
        logger.info("User '%s' is not in this group calendar", user_id)
        return {"message": "User not in group calendar"}, 200
    else:
        cal_doc["members"].remove(user_id)

    # 5) Upsert updated doc
    try:
        calendars_container.upsert_item(cal_doc)
        logger.info("User '%s' removed from group calendar '%s'", user_id, calendar_id)
        return {"message": "User removed successfully"}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error removing user from group calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500