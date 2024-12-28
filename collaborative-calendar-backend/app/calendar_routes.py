# app/calendar_routes.py

import logging
from datetime import datetime
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.database import calendars_container, events_container
from app.models import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def add_event(calendar_id: str, event_data: dict):
    """
    Adds a new event to a specified calendar.
    For personal calendars, event is locked by default.
    """
    logger.info("Adding event to calendar %s", calendar_id)

    # Validate that this calendar exists
    try:
        cal_query = list(calendars_container.query_items(
            query="SELECT * FROM Calendars c WHERE c.calendarId = @calId",
            parameters=[{"name":"@calId", "value": calendar_id}],
            enable_cross_partition_query=True
        ))
        if not cal_query:
            return {"error": "Calendar not found"}, 404
        calendar_doc = cal_query[0]
    except CosmosHttpResponseError as e:
        logger.exception("Error querying calendar %s: %s", calendar_id, str(e))
        return {"error": str(e)}, 500

    # Create the event model
    try:
        # We'll assume the input data has title, startTime, endTime, etc.
        # The event_data dict is coming from frontend.
        new_event = Event(**event_data)
        new_event.calendarId = calendar_id  # Enforce correct partition
        item_dict = new_event.dict()
        item_dict["id"] = new_event.eventId  # For Cosmos DB 'id'

        # Insert into Events container
        events_container.create_item(item_dict)
        logger.info("Event '%s' created in calendar '%s'", new_event.eventId, calendar_id)
        return {"message": "Event created successfully", "eventId": new_event.eventId}, 201

    except Exception as e:
        logger.exception("Error creating event in calendar %s: %s", calendar_id, str(e))
        return {"error": str(e)}, 500
