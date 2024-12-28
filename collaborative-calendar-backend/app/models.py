# app/models.py

from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

# -----------------------
# User Model
# -----------------------
class User(BaseModel):
    username: str # e.g., "johndoe"
    password: str # hashed password
    email: Optional[str] = None # optional field
    userId: str = str(uuid.uuid4()) # unique identifier for the user
    calendars: List[str] = []  # store calendarIds the user has

# -----------------------
# Calendar Model
# -----------------------
class Calendar(BaseModel):
    calendarId: str = str(uuid.uuid4())
    name: str  # e.g., "John Doe's Personal Calendar"
    ownerId: str  # which user created/owns this calendar
    isGroup: bool = False  # personal vs. group
    members: List[str] = []  # for group calendars, store member userIds

# -----------------------
# Event Model
# -----------------------
class Event(BaseModel):
    eventId: str = str(uuid.uuid4())
    calendarId: str  # which calendar this event belongs to
    title: str # e.g., "Meeting with John"
    startTime: datetime # e.g., 2021-08-01T09:00:00
    endTime: datetime # e.g., 2021-08-01T10:00:00
    locked: bool = True  # personal events are locked by default
    description: Optional[str] = None # e.g., "Discuss project timelines"


class Config:
    # Not strictly required, but helpful if you do new_event.json()
    # This instructs Pydantic how to encode datetimes
    json_encoders = {
        datetime: lambda dt: dt.isoformat()
    }