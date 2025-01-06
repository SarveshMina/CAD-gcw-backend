# app/models.py

from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

# -----------------------
# User Model
# -----------------------
class User(BaseModel):
    username: str  # e.g., "johndoe"
    password: str  # hashed password
    email: Optional[str] = None  # optional field
    userId: str = Field(default_factory=lambda: str(uuid.uuid4()))  # unique identifier for the user
    calendars: List[str] = []  # store calendarIds the user has
    default_calendar_id: str = ""  # store the default calendarId for the user

# -----------------------
# Calendar Model
# -----------------------
class Calendar(BaseModel):
    calendarId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "John Doe's Personal Calendar"
    ownerId: str  # which user created/owns this calendar
    isGroup: bool = False  # personal vs. group
    isDefault: bool = False  # marks the default (home) calendar
    members: List[str] = []  # for group calendars, store member userIds

# -----------------------
# Event Model
# -----------------------
class Event(BaseModel):
    eventId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    calendarId: str  # which calendar this event belongs to
    title: str  # e.g., "Meeting with John"
    startTime: datetime  # e.g., 2021-08-01T09:00:00
    endTime: datetime  # e.g., 2021-08-01T10:00:00
    locked: bool = True  # personal events are locked by default
    description: Optional[str] = None  # e.g., "Discuss project timelines"
    creatorId: str = ""  # to store who created the event
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.replace(second=0, microsecond=0).isoformat()
        }
