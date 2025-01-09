# app/calendar_routes.py

import logging
import json
from datetime import datetime
from typing import Tuple, List

from pydantic import ValidationError
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.database import calendars_container, events_container, user_container
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

# backend/app/calendar_routes.py

def get_user_calendars(user_id: str) -> Tuple[dict, int]:
    """
    Retrieves all calendars where the user is a member, including member usernames.
    """
    logger.info("Fetching calendars for user '%s'", user_id)
    try:
        # Fetch calendars where user is a member
        calendars_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE ARRAY_CONTAINS(c.members, @userId)",
            parameters=[{"name": "@userId", "value": user_id}],
            enable_cross_partition_query=True
        ))
        
        # For each calendar, fetch member usernames
        for cal in calendars_query:
            member_usernames = []
            for member_id in cal.get("members", []):
                user_query = list(user_container.query_items(
                    query="SELECT c.username FROM Users c WHERE c.userId = @userId",
                    parameters=[{"name": "@userId", "value": member_id}],
                    enable_cross_partition_query=True
                ))
                if user_query:
                    member_usernames.append(user_query[0]['username'])
                else:
                    member_usernames.append(member_id)  # Fallback to userId if username not found
            cal["memberUsernames"] = member_usernames
        
        return {"calendars": calendars_query}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching user calendars: %s", str(e))
        return {"error": "Failed to fetch user calendars."}, 500



def edit_group_calendar(calendar_id: str, admin_id: str, updated_data: dict) -> Tuple[dict, int]:
    """
    Admin can edit the group calendar's name and color.
    Only the owner (admin) can perform this action.
    """
    logger.info("Admin '%s' is editing group calendar '%s'", admin_id, calendar_id)

    # 1) Fetch calendar document
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
        return {"error": "Only group calendars can be edited"}, 400

    # 3) Check if the admin_id is the owner
    if cal_doc.get("ownerId") != admin_id:
        return {"error": "Only the calendar owner can edit the calendar"}, 403

    # 4) Update name and/or color
    allowed_colors = [color.value for color in CalendarColor if color != CalendarColor.blue]
    updated = False

    if "name" in updated_data:
        new_name = updated_data["name"].strip()
        if not new_name:
            return {"error": "Calendar name cannot be empty"}, 400
        cal_doc["name"] = new_name
        updated = True

    if "color" in updated_data:
        new_color = updated_data["color"]
        if new_color not in allowed_colors:
            logger.warning("Invalid color '%s' for calendar '%s'", new_color, calendar_id)
            return {"error": f"Invalid color. Allowed colors are: {', '.join(allowed_colors)}"}, 400
        cal_doc["color"] = new_color
        updated = True

    if not updated:
        return {"error": "No valid fields to update"}, 400

    # 5) Upsert the updated calendar
    try:
        calendars_container.upsert_item(cal_doc)
        logger.info("Group calendar '%s' updated successfully", calendar_id)
        return {"message": "Group calendar updated successfully"}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error updating group calendar '%s': %s", calendar_id, str(e))
        return {"error": str(e)}, 500
    
def leave_group_calendar(calendar_id: str, user_id: str) -> Tuple[dict, int]:
    """
    User can leave a group calendar. If the user is the owner, prevent leaving.
    """
    logger.info("User '%s' is attempting to leave group calendar '%s'", user_id, calendar_id)

    # 1) Fetch calendar document
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
        return {"error": "Only group calendars can be left"}, 400

    # 3) Check if the user is a member
    if user_id not in cal_doc.get("members", []):
        return {"error": "User is not a member of this calendar"}, 400

    # 4) Check if the user is the owner
    if cal_doc.get("ownerId") == user_id:
        return {"error": "Calendar owner cannot leave the calendar"}, 403

    # 5) Remove user from members list
    cal_doc["members"].remove(user_id)

    # 6) Upsert the updated calendar
    try:
        calendars_container.upsert_item(cal_doc)
        logger.info("User '%s' left group calendar '%s' successfully", user_id, calendar_id)
        return {"message": "You have left the group calendar successfully"}, 200
    except CosmosHttpResponseError as e:
        logger.exception("Error updating group calendar '%s' after user leave: %s", calendar_id, str(e))
        return {"error": str(e)}, 500


def get_all_events_for_user(user_id: str):
    """
    Fetches all events across all calendars the user is a member of.
    Returns a list of event dictionaries.
    """
    try:
        # 1. Get all calendars where the user is a member
        query = "SELECT * FROM c WHERE ARRAY_CONTAINS(c.members, @userId)"
        parameters = [{"name": "@userId", "value": user_id}]
        calendars = list(calendars_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        calendar_ids = [cal['calendarId'] for cal in calendars]
        
        if not calendar_ids:
            return []
        
        # 2. Fetch all events from these calendars
        # Cosmos DB SQL API doesn't support array parameters directly, so we'll construct a dynamic query
        # For simplicity, we'll fetch events per calendar and aggregate them
        all_events = []
        for cal_id in calendar_ids:
            event_query = "SELECT * FROM e WHERE e.calendarId = @calId"
            event_params = [{"name": "@calId", "value": cal_id}]
            events = list(events_container.query_items(
                query=event_query,
                parameters=event_params,
                enable_cross_partition_query=True
            ))
            all_events.extend(events)
        
        return all_events
    except CosmosHttpResponseError as e:
        logger.exception("Error fetching events for user '%s': %s", user_id, str(e))
        return []


def get_user_events(user_id: str) -> Tuple[List[dict], int]:
    """
    Retrieves all events from all calendars where the user is a member.
    """
    try:
        # Fetch all calendars where the user is a member (both personal and group)
        calendars = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE ARRAY_CONTAINS(c.members, @userId)",
            parameters=[{"name": "@userId", "value": user_id}],
            enable_cross_partition_query=True
        ))
        if not calendars:
            logger.warning("User '%s' does not have any calendars.", user_id)
            return [], 404

        calendar_ids = [cal["calendarId"] for cal in calendars]

        # Fetch all events from these calendars
        all_events = []
        for cal_id in calendar_ids:
            events = list(events_container.query_items(
                query="SELECT * FROM Events e WHERE e.calendarId = @calId",
                parameters=[{"name": "@calId", "value": cal_id}],
                enable_cross_partition_query=True
            ))
            all_events.extend(events)

        return all_events, 200

    except CosmosHttpResponseError as e:
        logger.exception("Error fetching events for user '%s': %s", user_id, str(e))
        return [], 500

    
def has_time_conflict(existing_events: list, new_start: datetime, new_end: datetime):
    """
    Checks if the new event time overlaps with any existing events.
    """
    for event in existing_events:
        event_start = event.get("startTime")
        event_end = event.get("endTime")
        if not event_start or not event_end:
            continue  # Skip events with invalid times

        # Ensure datetime objects
        if isinstance(event_start, str):
            event_start = datetime.fromisoformat(event_start)
        if isinstance(event_end, str):
            event_end = datetime.fromisoformat(event_end)

        # Check for overlap
        latest_start = max(new_start, event_start)
        earliest_end = min(new_end, event_end)
        delta = (earliest_end - latest_start).total_seconds()
        if delta > 0:
            return True  # Overlap found
    return False  # No overlap


# app/calendar_routes.py

def add_event(calendar_id: str, event_data: dict, user_id: str) -> Tuple[dict, int]:
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

    # 3) If it's a group calendar, perform conflict checks
    if cal_doc.get("isGroup"):
        members = cal_doc.get("members", [])
        new_event_start = event_data.get("startTime")
        new_event_end = event_data.get("endTime")

        if not new_event_start or not new_event_end:
            logger.warning("Event startTime or endTime missing.")
            return {"error": "Event startTime and endTime are required."}, 400

        # Convert to datetime if necessary
        if isinstance(new_event_start, str):
            try:
                new_event_start = datetime.fromisoformat(new_event_start)
            except ValueError:
                logger.warning("Invalid startTime format: %s", new_event_start)
                return {"error": "Invalid startTime format."}, 400
        if isinstance(new_event_end, str):
            try:
                new_event_end = datetime.fromisoformat(new_event_end)
            except ValueError:
                logger.warning("Invalid endTime format: %s", new_event_end)
                return {"error": "Invalid endTime format."}, 400

        busy_members_details = []

        for member_id in members:
            events, status = get_user_events(member_id)
            if status != 200:
                logger.error("Failed to fetch events for user '%s'", member_id)
                return {"error": f"Failed to fetch events for user '{member_id}'"}, 500

            for event in events:
                event_start = event.get("startTime")
                event_end = event.get("endTime")
                if not event_start or not event_end:
                    continue

                # Convert to datetime if necessary
                if isinstance(event_start, str):
                    try:
                        event_start = datetime.fromisoformat(event_start)
                    except ValueError:
                        continue  # Skip invalid formats
                if isinstance(event_end, str):
                    try:
                        event_end = datetime.fromisoformat(event_end)
                    except ValueError:
                        continue  # Skip invalid formats

                # Check for overlap
                latest_start = max(new_event_start, event_start)
                earliest_end = min(new_event_end, event_end)
                delta = (earliest_end - latest_start).total_seconds()
                if delta > 0:
                    # Fetch username
                    member_query = list(user_container.query_items(
                        query="SELECT * FROM Users u WHERE u.userId = @userId",
                        parameters=[{"name": "@userId", "value": member_id}],
                        enable_cross_partition_query=True
                    ))
                    if member_query:
                        username = member_query[0].get("username", member_id)
                    else:
                        username = member_id
                    busy_members_details.append({
                        "username": username,
                        "conflicting_event": event.get("title", "Unnamed Event"),
                        "startTime": event_start.isoformat(),
                        "endTime": event_end.isoformat()
                    })

        if busy_members_details:
            error_message = "Cannot create event. The following user(s) are busy at the selected time:\n"
            for member in busy_members_details:
                error_message += f"- {member['username']} during '{member['conflicting_event']}' from {member['startTime']} to {member['endTime']}.\n"
            logger.info(error_message)
            return {"error": error_message}, 409  # 409 Conflict

    # 4) Inject 'calendarId' into event_data
    event_data['calendarId'] = calendar_id  # Add calendarId to event_data

    # 5) Set 'creatorId' to 'user_id'
    event_data['creatorId'] = user_id

    # 6) Create the event doc
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