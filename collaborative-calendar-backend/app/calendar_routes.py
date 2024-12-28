# app/calendar_routes.py

import logging
from datetime import datetime
from pydantic import ValidationError
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.database import calendars_container, events_container
from app.models import Event

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
