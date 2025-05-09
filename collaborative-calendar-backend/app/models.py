# app/models.py

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime
from enum import Enum  # Import Enum

# -----------------------
# User Model
# -----------------------
class User(BaseModel):
    username: str  # e.g., "johndoe"
    password: Optional[str] = ""  # hashed password or empty if using Google OAuth
    email: EmailStr  # using Pydantic's EmailStr for validation
    userId: str = Field(default_factory=lambda: str(uuid.uuid4()))  # unique identifier for the user
    calendars: List[str] = []  # store calendarIds the user has
    default_calendar_id: str = ""  # store the default calendarId for the user
    googleId: Optional[str] = ""  # Google OAuth ID

    class Config:
        allow_population_by_field_name = True

# -----------------------
# Calendar Color Enum
# -----------------------
class CalendarColor(str, Enum):
    blue = "blue"
    pink = "pink"
    green = "green"
    yellow = "yellow"
    red = "red"
    purple = "purple"
    orange = "orange"

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
    color: CalendarColor = "blue"  # default color is blue

    class Config:
        use_enum_values = True  # Ensures enums are serialized as their values

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
    # isRecurring: bool = False
    # recurrenceFrequency: Optional[str] = None  # e.g. "daily", "weekly", "monthly"
    # recurrenceInterval: Optional[int] = 1  # how many days/weeks between occurrences
    # recurrenceCount: Optional[int] = None  # total number of occurrences
    # seriesId: Optional[str] = None  # ID linking all occurrences in a series

    class Config:
        json_encoders = {
            datetime: lambda v: v.replace(second=0, microsecond=0).isoformat()
        }

