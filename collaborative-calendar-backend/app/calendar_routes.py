# app/calendar_routes.py

import logging
import json
from datetime import datetime
from pydantic import ValidationError
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.database import calendars_container, events_container, user_container  # Added user_container
from app.models import Event, Calendar, CalendarColor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def create_personal_calendar(user_id: str, name: str, color: str):
    """
    create_personal_calendar:
    Creates a new calendar with isGroup=False and isDefault=False.
    Associates the calendar with the user by setting ownerId and including the user in members.
    """
    logger.info("Creating personal calendar '%s' for user '%s' with color '%s'", name, user_id, color)

    # Define allowed colors excluding 'blue'
    allowed_colors = [color.value for color in CalendarColor if color != CalendarColor.blue]
    if color not in allowed_colors:
        logger.warning("Invalid color '%s' for calendar '%s'", color, name)
        return {"error": f"Invalid color. Allowed colors are: {', '.join(allowed_colors)}"}, 400

    # Create the Calendar model
    personal_cal = Calendar(
        name=name,
        ownerId=user_id,
        isGroup=False,
        isDefault=False,  # Not a default calendar
        members=[user_id],
        color=color
    )
    cal_item = personal_cal.dict()
    cal_item["id"] = personal_cal.calendarId  # Cosmos 'id' fix

    try:
        calendars_container.create_item(cal_item)
        logger.info("Personal calendar '%s' created with ID '%s' and color '%s'", name, personal_cal.calendarId, color)
        return {
            "message": "Personal calendar created successfully",
            "calendarId": personal_cal.calendarId
        }, 201
    except CosmosHttpResponseError as e:
        logger.exception("Error creating personal calendar: %s", str(e))
        return {"error": str(e)}, 500


def delete_personal_calendar(user_id: str, calendar_id: str):
    """
    delete_personal_calendar:
    Verifies that the calendar exists and that the requesting user is the owner.
    Prevents deletion if the calendar is marked as isDefault=True.
    Deletes all events associated with the calendar before deleting the calendar itself.
    """
    logger.info("User '%s' attempting to delete calendar '%s'", user_id, calendar_id)

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

    # 2) Check if the user is the owner
    if cal_doc.get("ownerId") != user_id:
        return {"error": "Only the calendar owner can delete this calendar"}, 403

    # 3) Prevent deletion of the default calendar
    if cal_doc.get("isDefault"):
        return {"error": "Cannot delete the default home calendar"}, 400

    # 4) Delete associated events
    try:
        events_query = list(events_container.query_items(
            query="SELECT * FROM Events e WHERE e.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        for event in events_query:
            events_container.delete_item(item=event["id"], partition_key=event["calendarId"])
        logger.info("All events associated with calendar '%s' have been deleted", calendar_id)
    except CosmosHttpResponseError as e:
        logger.exception("Error deleting events for calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

    # 5) Delete the calendar
    try:
        calendars_container.delete_item(item=cal_doc["id"], partition_key=calendar_id)
        logger.info("Calendar '%s' deleted successfully", calendar_id)
        return {"message": "Personal calendar deleted successfully"}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error deleting calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

def get_user_calendars(user_id: str):
    """
    Retrieves all calendars where the user is a member.
    """
    try:
        query = "SELECT * FROM Calendars c WHERE ARRAY_CONTAINS(c.members, @userId)"
        parameters = [{"name": "@userId", "value": user_id}]
        calendars = list(calendars_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return {"calendars": calendars}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching calendars for user '%s': %s", user_id, str(e))
        return {"error": str(e)}, 500

def add_event(calendar_id: str, event_data: dict, user_id: str):
    logger.info("Adding event to calendar %s by user %s", calendar_id, user_id)

    # 1) Verify calendar
    try:
        cal_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE c.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        if not cal_query:
            logger.warning("Calendar '%s' not found.", calendar_id)
            return {"error": "Calendar not found"}, 404

        cal_doc = cal_query[0]
    except CosmosHttpResponseError as e:
        logger.exception("Error querying calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

    # 2) Check if user is a member of the calendar
    if user_id not in cal_doc.get("members", []):
        logger.warning("User '%s' is not a member of calendar '%s'", user_id, calendar_id)
        return {"error": "User is not a member of this calendar"}, 403

    # 3) Inject 'calendarId' into event_data
    event_data['calendarId'] = calendar_id  # Add calendarId to event_data

    # 4) Set 'creatorId' to 'user_id'
    event_data['creatorId'] = user_id

    # 5) Create the event doc
    try:
        new_event = Event(**event_data)  # Now calendarId and creatorId are included

        # Serialize the Event object to JSON and then back to dict to ensure all fields are serializable
        event_json = new_event.json()
        item_dict = json.loads(event_json)
        item_dict["id"] = new_event.eventId  # Set 'id' for Cosmos

        # Debug log to inspect the serialized item_dict
        logger.debug("Serialized event data: %s", json.dumps(item_dict, indent=2))

        events_container.create_item(item_dict)
        logger.info("Event '%s' created in calendar '%s'", new_event.eventId, calendar_id)
        return {"message": "Event created successfully", "eventId": new_event.eventId}, 201

    except ValidationError as ve:
        # Specific handling for missing/invalid fields
        logger.warning("Validation error for event in calendar '%s': %s", calendar_id, ve)
        return {"error": str(ve)}, 422

    except CosmosHttpResponseError as e:
        # Handle Cosmos DB specific errors
        logger.exception("Cosmos HTTP error while creating event: %s", str(e))
        return {"error": str(e)}, 500

    except Exception as e:
        # Catch-all for other issues
        logger.exception("Error creating event in calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500

def get_events(calendar_id: str, user_id: str):
    """
    Retrieve all events for the given calendar_id.
    Optionally, check if user_id is a member of this calendar.
    """
    logger.info("Fetching events for calendar %s by user %s", calendar_id, user_id)
    try:
        # 1) Fetch the calendar doc
        cal_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE c.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        if not cal_query:
            return {"error": "Calendar not found"}, 404

        cal_doc = cal_query[0]

        # 2) If you require user membership, check if user_id is in members
        if user_id and user_id not in cal_doc.get("members", []):
            logger.warning("User '%s' is not a member of calendar '%s'", user_id, calendar_id)
            return {"error": "User is not a member of this calendar"}, 403

        # 3) Query events by calendarId
        events_query = list(events_container.query_items(
            query="SELECT * FROM Events e WHERE e.calendarId = @calId",
            parameters=[{"name": "@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))

        return {"events": events_query}, 200

    except CosmosHttpResponseError as e:
        logger.exception("Error fetching events for calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500


def update_event(calendar_id: str, event_id: str, updated_data: dict, user_id: str):
    """
    Updates an existing event in a calendar.
    Ensures that the user is the creator of the event or has necessary permissions.
    """
    logger.info("Updating event '%s' in calendar '%s' by user '%s'", event_id, calendar_id, user_id)

    try:
        # Fetch the event document
        event_query = list(events_container.query_items(
            query="SELECT * FROM Events e WHERE e.eventId = @eventId AND e.calendarId = @calId",
            parameters=[
                {"name": "@eventId", "value": event_id},
                {"name": "@calId", "value": calendar_id}
            ],
            enable_cross_partition_query=True
        ))
        if not event_query:
            return {"error": "Event not found"}, 404

        event_doc = event_query[0]

        # Check if the user is the creator
        if event_doc.get("creatorId") != user_id:
            logger.warning("User '%s' is not the creator of event '%s'", user_id, event_id)
            return {"error": "Only the creator can update this event"}, 403

        # Update fields
        for key, value in updated_data.items():
            if key in event_doc and key not in ["eventId", "calendarId", "creatorId", "id"]:
                event_doc[key] = value

        # Upsert the updated event
        events_container.upsert_item(event_doc)
        logger.info("Event '%s' updated successfully in calendar '%s'", event_id, calendar_id)
        return {"message": "Event updated successfully"}, 200

    except CosmosHttpResponseError as e:
        logger.exception("Error updating event '%s' in calendar '%s': %s", event_id, calendar_id, str(e))
        return {"error": str(e)}, 500

def delete_event(calendar_id: str, event_id: str, user_id: str):
    """
    Deletes an event from a calendar.
    Ensures that the user is the creator of the event or has necessary permissions.
    """
    logger.info("Deleting event '%s' from calendar '%s' by user '%s'", event_id, calendar_id, user_id)

    try:
        # Fetch the event document
        event_query = list(events_container.query_items(
            query="SELECT * FROM Events e WHERE e.eventId = @eventId AND e.calendarId = @calId",
            parameters=[
                {"name": "@eventId", "value": event_id},
                {"name": "@calId", "value": calendar_id}
            ],
            enable_cross_partition_query=True
        ))
        if not event_query:
            return {"error": "Event not found"}, 404

        event_doc = event_query[0]

        # Check if the user is the creator
        if event_doc.get("creatorId") != user_id:
            logger.warning("User '%s' is not the creator of event '%s'", user_id, event_id)
            return {"error": "Only the creator can delete this event"}, 403

        # Delete the event
        events_container.delete_item(item=event_doc["id"], partition_key=calendar_id)
        logger.info("Event '%s' deleted successfully from calendar '%s'", event_id, calendar_id)
        return {"message": "Event deleted successfully"}, 200

    except CosmosHttpResponseError as e:
        logger.exception("Error deleting event '%s' from calendar '%s': %s", event_id, calendar_id, str(e))
        return {"error": str(e)}, 500


# Helper functions for creating group calendars
# and managing group members
def get_user_id(username: str):
    """
    Retrieves the userId for a given username.
    Returns None if the user does not exist.
    """
    try:
        user_query = list(user_container.query_items(
            query="SELECT * FROM Users u WHERE u.username = @username",
            parameters=[{"name": "@username", "value": username}],
            enable_cross_partition_query=True
        ))
        if not user_query:
            return None
        return user_query[0]["userId"]
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching user '%s': %s", username, str(e))
        return None



def create_group_calendar(owner_id: str, name: str, members_usernames: list, color: str):
    """
    Creates a new group calendar with specified members and color.
    """
    logger.info("Creating group calendar '%s' for owner '%s' with color '%s' and members %s", name, owner_id, color, members_usernames)

    # Define allowed colors excluding 'blue'
    allowed_colors = [color.value for color in CalendarColor if color != CalendarColor.blue]
    if color not in allowed_colors:
        logger.warning("Invalid color '%s' for group calendar '%s'", color, name)
        return {"error": f"Invalid color. Allowed colors are: {', '.join(allowed_colors)}"}, 400
    
    # 1. Validate owner exists
    try:
        owner_query = list(user_container.query_items(
            query="SELECT * FROM Users u WHERE u.userId = @userId",
            parameters=[{"name": "@userId", "value": owner_id}],
            enable_cross_partition_query=True
        ))
        if not owner_query:
            logger.warning("Owner with userId '%s' does not exist.", owner_id)
            return {"error": "Owner does not exist"}, 404
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching owner '%s': %s", owner_id, str(e))
        return {"error": str(e)}, 500
    
    # 2. Map member usernames to userIds
    member_ids = []
    for username in members_usernames:
        user_id = get_user_id(username)
        if not user_id:
            logger.warning("Member username '%s' does not exist.", username)
            return {"error": f"User '{username}' does not exist"}, 404
        member_ids.append(user_id)
    
    # 3. Include owner in members if not already present
    if owner_id not in member_ids:
        member_ids.append(owner_id)
    
    # 4. Enforce maximum of 5 members
    if len(member_ids) > 5:
        logger.warning("Attempted to create group calendar with %d members. Maximum allowed is 5.", len(member_ids))
        return {"error": "Cannot have more than 5 members in a group calendar"}, 400
    
    # 5. Create the Calendar model
    # Create the Calendar model
    group_cal = Calendar(
        name=name,
        ownerId=owner_id,
        isGroup=True,
        members=member_ids,
        color=color
    )
    cal_item = group_cal.dict()
    cal_item["id"] = group_cal.calendarId  # Cosmos 'id' fix

    try:
        calendars_container.create_item(cal_item)
        logger.info("Group calendar '%s' created with ID '%s' and color '%s'", name, group_cal.calendarId, color)
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